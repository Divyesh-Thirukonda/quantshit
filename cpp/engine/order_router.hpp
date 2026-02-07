#pragma once

/**
 * Order Router
 *
 * Smart order routing across multiple venues with latency optimization,
 * venue selection, and execution splitting.
 */

#include <algorithm>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "execution_engine.hpp"
#include "market_data_handler.hpp"

namespace quantshit {

/**
 * Venue routing statistics for smart routing decisions
 */
struct VenueStats {
  Protocol venue;
  int64_t avg_latency_ns;
  int64_t p99_latency_ns;
  double fill_rate;   // Percentage of orders that get filled
  double reject_rate; // Percentage of orders rejected
  double available_liquidity;
  int64_t last_update_ns;
};

/**
 * Routing strategy
 */
enum class RoutingStrategy {
  BEST_PRICE,     // Route to venue with best price
  LOWEST_LATENCY, // Route to venue with lowest latency
  BEST_FILL_RATE, // Route to venue with highest fill rate
  SMART,          // Consider all factors
  SPLIT           // Split across venues
};

/**
 * Routing decision
 */
struct RoutingDecision {
  Protocol primary_venue;
  std::vector<std::pair<Protocol, double>>
      venue_splits; // venue -> quantity fraction
  std::string reason;
};

/**
 * Order router for multi-venue execution
 */
class OrderRouter {
public:
  struct Config {
    RoutingStrategy default_strategy;
    double min_split_size;   // Minimum size before splitting
    double latency_weight;   // Weight for latency in smart routing
    double price_weight;     // Weight for price
    double fill_rate_weight; // Weight for fill rate
    // Explicit constructor to satisfy AppleClang nested struct requirements
    Config()
        : default_strategy(RoutingStrategy::SMART), min_split_size(100.0),
          latency_weight(0.3), price_weight(0.4), fill_rate_weight(0.3) {}
  };

  explicit OrderRouter(ExecutionEngine &engine, MarketDataHandler &market_data,
                       const Config &config = Config())
      : engine_(engine), market_data_(market_data), config_(config) {}

  /**
   * Route an order to optimal venue(s)
   */
  bool route_order(const OrderRequest &request,
                   RoutingStrategy strategy = RoutingStrategy::SMART) {
    auto decision = make_routing_decision(request, strategy);

    if (decision.venue_splits.size() <= 1) {
      // Single venue execution
      OrderRequest routed_request = request;
      routed_request.venue = decision.primary_venue;
      return engine_.submit_order(routed_request);
    }

    // Split execution across venues
    bool success = true;
    for (const auto &[venue, fraction] : decision.venue_splits) {
      OrderRequest split_request = request;
      split_request.venue = venue;
      split_request.quantity = request.quantity * fraction;

      if (split_request.quantity >= config_.min_split_size) {
        success &= engine_.submit_order(split_request);
      }
    }

    return success;
  }

  /**
   * Make routing decision without executing
   */
  RoutingDecision
  make_routing_decision(const OrderRequest &request,
                        RoutingStrategy strategy = RoutingStrategy::SMART) {

    RoutingDecision decision;

    switch (strategy) {
    case RoutingStrategy::BEST_PRICE:
      decision = route_by_price(request);
      break;
    case RoutingStrategy::LOWEST_LATENCY:
      decision = route_by_latency(request);
      break;
    case RoutingStrategy::BEST_FILL_RATE:
      decision = route_by_fill_rate(request);
      break;
    case RoutingStrategy::SPLIT:
      decision = route_split(request);
      break;
    case RoutingStrategy::SMART:
    default:
      decision = route_smart(request);
      break;
    }

    return decision;
  }

  /**
   * Update venue statistics
   */
  void update_venue_stats(Protocol venue, const VenueStats &stats) {
    venue_stats_[venue] = stats;
  }

  /**
   * Record execution for stats update
   */
  void record_execution(Protocol venue, int64_t latency_ns, bool filled,
                        bool rejected) {
    auto &stats = venue_stats_[venue];
    stats.venue = venue;

    // Update latency (exponential moving average)
    stats.avg_latency_ns = (stats.avg_latency_ns * 7 + latency_ns) / 8;
    if (latency_ns > stats.p99_latency_ns) {
      stats.p99_latency_ns = latency_ns;
    }

    // Update fill/reject rates
    total_orders_[venue]++;
    if (filled)
      filled_orders_[venue]++;
    if (rejected)
      rejected_orders_[venue]++;

    stats.fill_rate =
        static_cast<double>(filled_orders_[venue]) / total_orders_[venue];
    stats.reject_rate =
        static_cast<double>(rejected_orders_[venue]) / total_orders_[venue];
    stats.last_update_ns = now_ns();
  }

  /**
   * Get statistics for a venue
   */
  std::optional<VenueStats> get_venue_stats(Protocol venue) const {
    auto it = venue_stats_.find(venue);
    return it != venue_stats_.end() ? std::make_optional(it->second)
                                    : std::nullopt;
  }

private:
  RoutingDecision route_by_price(const OrderRequest &request) {
    RoutingDecision decision;
    double best_price =
        request.side == Side::BUY ? std::numeric_limits<double>::max() : 0.0;

    for (const auto &[venue, _] : venue_stats_) {
      auto quote = market_data_.get_quote(request.market_id);
      if (!quote)
        continue;

      double price =
          request.side == Side::BUY ? quote->ask_price : quote->bid_price;
      bool is_better = request.side == Side::BUY ? (price < best_price)
                                                 : (price > best_price);

      if (is_better) {
        best_price = price;
        decision.primary_venue = venue;
      }
    }

    decision.venue_splits.push_back({decision.primary_venue, 1.0});
    decision.reason = "Best price at venue";
    return decision;
  }

  RoutingDecision route_by_latency(const OrderRequest &request) {
    RoutingDecision decision;
    int64_t best_latency = std::numeric_limits<int64_t>::max();

    for (const auto &[venue, stats] : venue_stats_) {
      if (stats.avg_latency_ns < best_latency) {
        best_latency = stats.avg_latency_ns;
        decision.primary_venue = venue;
      }
    }

    if (venue_stats_.empty()) {
      decision.primary_venue = request.venue;
    }

    decision.venue_splits.push_back({decision.primary_venue, 1.0});
    decision.reason = "Lowest latency venue";
    return decision;
  }

  RoutingDecision
  route_by_fill_rate([[maybe_unused]] const OrderRequest &request) {
    RoutingDecision decision;
    double best_fill_rate = 0.0;

    for (const auto &[venue, stats] : venue_stats_) {
      if (stats.fill_rate > best_fill_rate) {
        best_fill_rate = stats.fill_rate;
        decision.primary_venue = venue;
      }
    }

    decision.venue_splits.push_back({decision.primary_venue, 1.0});
    decision.reason = "Best fill rate venue";
    return decision;
  }

  RoutingDecision route_split(const OrderRequest &request) {
    RoutingDecision decision;

    // Split evenly across all venues
    size_t num_venues = venue_stats_.size();
    if (num_venues == 0) {
      decision.primary_venue = request.venue;
      decision.venue_splits.push_back({request.venue, 1.0});
      return decision;
    }

    double fraction = 1.0 / num_venues;
    for (const auto &[venue, _] : venue_stats_) {
      decision.venue_splits.push_back({venue, fraction});
    }

    decision.primary_venue = decision.venue_splits[0].first;
    decision.reason = "Even split across venues";
    return decision;
  }

  RoutingDecision route_smart(const OrderRequest &request) {
    RoutingDecision decision;

    if (venue_stats_.empty()) {
      decision.primary_venue = request.venue;
      decision.venue_splits.push_back({request.venue, 1.0});
      decision.reason = "No venue stats available";
      return decision;
    }

    // Score each venue
    std::vector<std::pair<Protocol, double>> venue_scores;

    double max_latency = 0, max_fill = 0;
    for (const auto &[_, stats] : venue_stats_) {
      max_latency =
          std::max(max_latency, static_cast<double>(stats.avg_latency_ns));
      max_fill = std::max(max_fill, stats.fill_rate);
    }

    for (const auto &[venue, stats] : venue_stats_) {
      double latency_score =
          max_latency > 0
              ? 1.0 - (static_cast<double>(stats.avg_latency_ns) / max_latency)
              : 0.5;
      double fill_score = max_fill > 0 ? stats.fill_rate / max_fill : 0.5;

      // Get price score from market data
      double price_score = 0.5; // Default neutral
      auto quote = market_data_.get_quote(request.market_id);
      if (quote) {
        // In real implementation, compare across venues
        price_score = 0.5;
      }

      double total_score = config_.latency_weight * latency_score +
                           config_.fill_rate_weight * fill_score +
                           config_.price_weight * price_score;

      venue_scores.push_back({venue, total_score});
    }

    // Sort by score descending
    std::sort(venue_scores.begin(), venue_scores.end(),
              [](const auto &a, const auto &b) { return a.second > b.second; });

    decision.primary_venue = venue_scores[0].first;
    decision.venue_splits.push_back({decision.primary_venue, 1.0});
    decision.reason = "Smart routing based on combined metrics";

    return decision;
  }

  ExecutionEngine &engine_;
  MarketDataHandler &market_data_;
  Config config_;

  std::unordered_map<Protocol, VenueStats> venue_stats_;
  std::unordered_map<Protocol, uint64_t> total_orders_;
  std::unordered_map<Protocol, uint64_t> filled_orders_;
  std::unordered_map<Protocol, uint64_t> rejected_orders_;
};

} // namespace quantshit
