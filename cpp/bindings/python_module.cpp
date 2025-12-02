/**
 * Python Bindings for Quantshit C++ Engine
 *
 * Exposes high-performance C++ components to Python using pybind11.
 * Allows the existing Python ArbitrageBot to use C++ execution engine.
 */

#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../core/cpu_utils.hpp"
#include "../core/lock_free_queue.hpp"
#include "../core/timing.hpp"
#include "../engine/arbitrage_detector.hpp"
#include "../engine/execution_engine.hpp"
#include "../engine/market_data_handler.hpp"
#include "../engine/order_router.hpp"
#include "../network/packet_normalizer.hpp"
#include "../network/zmq_transport.hpp"

namespace py = pybind11;

PYBIND11_MODULE(quantshit_engine, m) {
  m.doc() = "Quantshit C++ Execution Engine - High-performance trading "
            "infrastructure";

  // ===== Core Module =====
  auto core = m.def_submodule("core", "Core utilities");

  // CPU utilities
  py::class_<quantshit::PinResult>(core, "PinResult")
      .def_readonly("success", &quantshit::PinResult::success)
      .def_readonly("error_code", &quantshit::PinResult::error_code)
      .def_readonly("message", &quantshit::PinResult::message)
      .def("__bool__", [](const quantshit::PinResult &r) { return r.success; });

  core.def("pin_to_core", &quantshit::pin_to_core, py::arg("core_id"),
           "Pin current thread to a specific CPU core");

  core.def("set_realtime_priority", &quantshit::set_realtime_priority,
           py::arg("priority"), "Set real-time scheduling priority (1-99)");

  core.def("get_num_cores", &quantshit::get_num_cores,
           "Get number of available CPU cores");

  core.def("now_ns", &quantshit::now_ns,
           "Get current timestamp in nanoseconds");

  core.def("now_us", &quantshit::now_us,
           "Get current timestamp in microseconds");

  // Latency stats
  py::class_<quantshit::LatencyStats>(core, "LatencyStats")
      .def(py::init<size_t>(), py::arg("reserve_size") = 10000)
      .def("record",
           py::overload_cast<int64_t>(&quantshit::LatencyStats::record))
      .def("count", &quantshit::LatencyStats::count)
      .def("min", &quantshit::LatencyStats::min)
      .def("max", &quantshit::LatencyStats::max)
      .def("mean", &quantshit::LatencyStats::mean)
      .def("stddev", &quantshit::LatencyStats::stddev)
      .def("p50", &quantshit::LatencyStats::p50)
      .def("p90", &quantshit::LatencyStats::p90)
      .def("p95", &quantshit::LatencyStats::p95)
      .def("p99", &quantshit::LatencyStats::p99)
      .def("p999", &quantshit::LatencyStats::p999)
      .def("jitter", &quantshit::LatencyStats::jitter)
      .def("reset", &quantshit::LatencyStats::reset)
      .def("summary", &quantshit::LatencyStats::summary);

  // ===== Network Module =====
  auto network = m.def_submodule("network", "Network transport layer");

  // Protocol enum
  py::enum_<quantshit::Protocol>(network, "Protocol")
      .value("UNKNOWN", quantshit::Protocol::UNKNOWN)
      .value("KALSHI_REST", quantshit::Protocol::KALSHI_REST)
      .value("KALSHI_WS", quantshit::Protocol::KALSHI_WS)
      .value("POLYMARKET_REST", quantshit::Protocol::POLYMARKET_REST)
      .value("POLYMARKET_WS", quantshit::Protocol::POLYMARKET_WS)
      .value("UNISWAP_V3", quantshit::Protocol::UNISWAP_V3)
      .value("DYDX", quantshit::Protocol::DYDX)
      .value("CUSTOM_DEX", quantshit::Protocol::CUSTOM_DEX)
      .export_values();

  // Side enum
  py::enum_<quantshit::Side>(network, "Side")
      .value("BUY", quantshit::Side::BUY)
      .value("SELL", quantshit::Side::SELL)
      .export_values();

  // MarketDataUpdate
  py::class_<quantshit::MarketDataUpdate>(network, "MarketDataUpdate")
      .def(py::init<>())
      .def_readwrite("source", &quantshit::MarketDataUpdate::source)
      .def_readwrite("market_id", &quantshit::MarketDataUpdate::market_id)
      .def_readwrite("symbol", &quantshit::MarketDataUpdate::symbol)
      .def_readwrite("bid_price", &quantshit::MarketDataUpdate::bid_price)
      .def_readwrite("ask_price", &quantshit::MarketDataUpdate::ask_price)
      .def_readwrite("bid_size", &quantshit::MarketDataUpdate::bid_size)
      .def_readwrite("ask_size", &quantshit::MarketDataUpdate::ask_size)
      .def_readwrite("last_price", &quantshit::MarketDataUpdate::last_price)
      .def_readwrite("timestamp_ns",
                     &quantshit::MarketDataUpdate::timestamp_ns);

  // ===== Engine Module =====
  auto engine = m.def_submodule("engine", "Execution engine components");

  // Order status and type enums
  py::enum_<quantshit::OrderStatus>(engine, "OrderStatus")
      .value("PENDING", quantshit::OrderStatus::PENDING)
      .value("SUBMITTED", quantshit::OrderStatus::SUBMITTED)
      .value("ACKNOWLEDGED", quantshit::OrderStatus::ACKNOWLEDGED)
      .value("PARTIALLY_FILLED", quantshit::OrderStatus::PARTIALLY_FILLED)
      .value("FILLED", quantshit::OrderStatus::FILLED)
      .value("CANCELLED", quantshit::OrderStatus::CANCELLED)
      .value("REJECTED", quantshit::OrderStatus::REJECTED)
      .value("ERROR", quantshit::OrderStatus::ERROR)
      .export_values();

  py::enum_<quantshit::OrderType>(engine, "OrderType")
      .value("MARKET", quantshit::OrderType::MARKET)
      .value("LIMIT", quantshit::OrderType::LIMIT)
      .value("IOC", quantshit::OrderType::IOC)
      .value("FOK", quantshit::OrderType::FOK)
      .value("GTC", quantshit::OrderType::GTC)
      .export_values();

  // Order
  py::class_<quantshit::Order>(engine, "Order")
      .def(py::init<>())
      .def_readwrite("internal_id", &quantshit::Order::internal_id)
      .def_readwrite("external_id", &quantshit::Order::external_id)
      .def_readwrite("market_id", &quantshit::Order::market_id)
      .def_readwrite("venue", &quantshit::Order::venue)
      .def_readwrite("side", &quantshit::Order::side)
      .def_readwrite("type", &quantshit::Order::type)
      .def_readwrite("status", &quantshit::Order::status)
      .def_readwrite("price", &quantshit::Order::price)
      .def_readwrite("quantity", &quantshit::Order::quantity)
      .def_readwrite("filled_quantity", &quantshit::Order::filled_quantity);

  // OrderRequest
  py::class_<quantshit::OrderRequest>(engine, "OrderRequest")
      .def(py::init<>())
      .def_readwrite("market_id", &quantshit::OrderRequest::market_id)
      .def_readwrite("venue", &quantshit::OrderRequest::venue)
      .def_readwrite("side", &quantshit::OrderRequest::side)
      .def_readwrite("type", &quantshit::OrderRequest::type)
      .def_readwrite("price", &quantshit::OrderRequest::price)
      .def_readwrite("quantity", &quantshit::OrderRequest::quantity);

  // ExecutionReport
  py::class_<quantshit::ExecutionReport>(engine, "ExecutionReport")
      .def(py::init<>())
      .def_readwrite("order_id", &quantshit::ExecutionReport::order_id)
      .def_readwrite("external_id", &quantshit::ExecutionReport::external_id)
      .def_readwrite("status", &quantshit::ExecutionReport::status)
      .def_readwrite("filled_quantity",
                     &quantshit::ExecutionReport::filled_quantity)
      .def_readwrite("fill_price", &quantshit::ExecutionReport::fill_price)
      .def_readwrite("message", &quantshit::ExecutionReport::message);

  // RiskLimits
  py::class_<quantshit::RiskLimits>(engine, "RiskLimits")
      .def(py::init<>())
      .def_readwrite("max_order_size", &quantshit::RiskLimits::max_order_size)
      .def_readwrite("max_position_per_market",
                     &quantshit::RiskLimits::max_position_per_market)
      .def_readwrite("max_total_position",
                     &quantshit::RiskLimits::max_total_position)
      .def_readwrite("max_orders_per_second",
                     &quantshit::RiskLimits::max_orders_per_second)
      .def_readwrite("max_loss_per_day",
                     &quantshit::RiskLimits::max_loss_per_day);

  // ExecutionEngine::Config
  py::class_<quantshit::ExecutionEngine::Config>(engine,
                                                 "ExecutionEngineConfig")
      .def(py::init<>())
      .def_readwrite("order_thread_core",
                     &quantshit::ExecutionEngine::Config::order_thread_core)
      .def_readwrite(
          "market_data_thread_core",
          &quantshit::ExecutionEngine::Config::market_data_thread_core)
      .def_readwrite("order_queue_size",
                     &quantshit::ExecutionEngine::Config::order_queue_size)
      .def_readwrite("risk_limits",
                     &quantshit::ExecutionEngine::Config::risk_limits);

  // ExecutionEngine
  py::class_<quantshit::ExecutionEngine>(engine, "ExecutionEngine")
      .def(py::init<const quantshit::ExecutionEngine::Config &>(),
           py::arg("config") = quantshit::ExecutionEngine::Config())
      .def("start", &quantshit::ExecutionEngine::start)
      .def("stop", &quantshit::ExecutionEngine::stop)
      .def("submit_order", &quantshit::ExecutionEngine::submit_order)
      .def("cancel_order", &quantshit::ExecutionEngine::cancel_order)
      .def("get_order", &quantshit::ExecutionEngine::get_order);

  // Quote
  py::class_<quantshit::Quote>(engine, "Quote")
      .def(py::init<>())
      .def_readwrite("market_id", &quantshit::Quote::market_id)
      .def_readwrite("source", &quantshit::Quote::source)
      .def_readwrite("bid_price", &quantshit::Quote::bid_price)
      .def_readwrite("bid_size", &quantshit::Quote::bid_size)
      .def_readwrite("ask_price", &quantshit::Quote::ask_price)
      .def_readwrite("ask_size", &quantshit::Quote::ask_size)
      .def_readwrite("timestamp_ns", &quantshit::Quote::timestamp_ns)
      .def("mid_price", &quantshit::Quote::mid_price)
      .def("spread", &quantshit::Quote::spread);

  // MarketDataHandler
  py::class_<quantshit::MarketDataHandler>(engine, "MarketDataHandler")
      .def(py::init<const quantshit::MarketDataHandler::Config &>(),
           py::arg("config") = quantshit::MarketDataHandler::Config())
      .def("start", &quantshit::MarketDataHandler::start)
      .def("stop", &quantshit::MarketDataHandler::stop)
      .def("get_quote", &quantshit::MarketDataHandler::get_quote)
      .def("get_markets", &quantshit::MarketDataHandler::get_markets);

  // ArbitrageOpportunity
  py::class_<quantshit::ArbitrageOpportunity>(engine, "ArbitrageOpportunity")
      .def(py::init<>())
      .def_readwrite("market_id", &quantshit::ArbitrageOpportunity::market_id)
      .def_readwrite("buy_venue", &quantshit::ArbitrageOpportunity::buy_venue)
      .def_readwrite("sell_venue", &quantshit::ArbitrageOpportunity::sell_venue)
      .def_readwrite("buy_price", &quantshit::ArbitrageOpportunity::buy_price)
      .def_readwrite("sell_price", &quantshit::ArbitrageOpportunity::sell_price)
      .def_readwrite("spread_bps", &quantshit::ArbitrageOpportunity::spread_bps)
      .def_readwrite("expected_profit",
                     &quantshit::ArbitrageOpportunity::expected_profit)
      .def_readwrite("profit_after_fees",
                     &quantshit::ArbitrageOpportunity::profit_after_fees)
      .def_readwrite("confidence",
                     &quantshit::ArbitrageOpportunity::confidence);

  // ArbitrageDetector
  py::class_<quantshit::ArbitrageDetector>(engine, "ArbitrageDetector")
      .def(py::init<quantshit::MarketDataHandler &,
                    const quantshit::ArbitrageConfig &>(),
           py::arg("market_data"),
           py::arg("config") = quantshit::ArbitrageConfig())
      .def("start", &quantshit::ArbitrageDetector::start)
      .def("stop", &quantshit::ArbitrageDetector::stop)
      .def("check_market", &quantshit::ArbitrageDetector::check_market)
      .def("get_opportunities",
           &quantshit::ArbitrageDetector::get_opportunities)
      .def("get_best_opportunity",
           &quantshit::ArbitrageDetector::get_best_opportunity);

  // ===== Version Info =====
  m.attr("__version__") = "1.0.0";
  m.attr("__author__") = "Quantshit Team";
}
