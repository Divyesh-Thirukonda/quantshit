#pragma once

/**
 * Packet Normalizer
 *
 * Transforms raw network packets from various market protocols into
 * a unified internal representation. Handles byte-order conversion,
 * field extraction, and protocol-specific parsing.
 */

#include <arpa/inet.h>
#include <cstdint>
#include <cstring>
#include <optional>
#include <stdexcept>
#include <string>
#include <variant>
#include <vector>

namespace quantshit {

/**
 * Supported market protocols
 */
enum class Protocol : uint8_t {
  UNKNOWN = 0,
  KALSHI_REST = 1,
  KALSHI_WS = 2,
  POLYMARKET_REST = 3,
  POLYMARKET_WS = 4,
  UNISWAP_V3 = 5,
  DYDX = 6,
  CUSTOM_DEX = 7
};

/**
 * Order side
 */
enum class Side : uint8_t { BUY = 0, SELL = 1 };

/**
 * Normalized market data update
 */
struct MarketDataUpdate {
  Protocol source;
  std::string market_id;
  std::string symbol;

  double bid_price;
  double ask_price;
  double bid_size;
  double ask_size;
  double last_price;
  double volume_24h;

  int64_t timestamp_ns;
  uint32_t sequence;
};

/**
 * Normalized order book level
 */
struct BookLevel {
  double price;
  double size;
  int64_t timestamp_ns;
};

/**
 * Normalized order book snapshot
 */
struct OrderBookSnapshot {
  Protocol source;
  std::string market_id;

  std::vector<BookLevel> bids; // Sorted price descending
  std::vector<BookLevel> asks; // Sorted price ascending

  int64_t timestamp_ns;
  uint32_t sequence;
};

/**
 * Normalized trade event
 */
struct TradeEvent {
  Protocol source;
  std::string market_id;
  std::string trade_id;

  Side aggressor_side;
  double price;
  double size;

  int64_t timestamp_ns;
};

/**
 * Normalized order fill
 */
struct OrderFill {
  Protocol source;
  std::string order_id;
  std::string market_id;

  Side side;
  double price;
  double filled_size;
  double remaining_size;

  bool is_complete;
  int64_t timestamp_ns;
};

/**
 * Union of all normalized message types
 */
using NormalizedMessage =
    std::variant<MarketDataUpdate, OrderBookSnapshot, TradeEvent, OrderFill>;

/**
 * Raw packet buffer with protocol context
 */
struct RawPacket {
  Protocol protocol;
  std::vector<uint8_t> data;
  int64_t recv_timestamp_ns;
};

/**
 * Byte order conversion utilities
 */
inline uint16_t ntoh16(const uint8_t *data) {
  return ntohs(*reinterpret_cast<const uint16_t *>(data));
}

inline uint32_t ntoh32(const uint8_t *data) {
  return ntohl(*reinterpret_cast<const uint32_t *>(data));
}

inline uint64_t ntoh64(const uint8_t *data) {
  uint64_t val;
  memcpy(&val, data, sizeof(val));
  return __builtin_bswap64(val);
}

inline double ntoh_double(const uint8_t *data) {
  uint64_t bits = ntoh64(data);
  double val;
  memcpy(&val, &bits, sizeof(val));
  return val;
}

/**
 * Base protocol parser interface
 */
class ProtocolParser {
public:
  virtual ~ProtocolParser() = default;

  virtual Protocol protocol() const = 0;
  virtual std::optional<NormalizedMessage> parse(const RawPacket &packet) = 0;
};

/**
 * JSON-based protocol parser for REST APIs
 */
class JsonProtocolParser : public ProtocolParser {
public:
  Protocol protocol() const override { return Protocol::UNKNOWN; }

  std::optional<NormalizedMessage> parse(const RawPacket &packet) override {
    // Parse JSON from packet.data
    // This is a simplified implementation - real version would use rapidjson
    std::string json(packet.data.begin(), packet.data.end());

    // TODO: Implement actual JSON parsing
    // For now, return empty
    return std::nullopt;
  }
};

/**
 * Kalshi market data parser
 */
class KalshiParser : public ProtocolParser {
public:
  Protocol protocol() const override { return Protocol::KALSHI_WS; }

  std::optional<NormalizedMessage> parse(const RawPacket &packet) override {
    if (packet.data.size() < 8) {
      return std::nullopt;
    }

    // Kalshi WebSocket format (simplified):
    // [2 bytes: msg_type] [2 bytes: flags] [4 bytes: sequence] [payload...]

    uint16_t msg_type = ntoh16(packet.data.data());
    [[maybe_unused]] uint16_t flags = ntoh16(packet.data.data() + 2);
    uint32_t sequence = ntoh32(packet.data.data() + 4);

    switch (msg_type) {
    case 0x0001: // Quote update
      return parse_quote(packet, sequence);
    case 0x0002: // Trade
      return parse_trade(packet, sequence);
    case 0x0003: // Book snapshot
      return parse_book(packet, sequence);
    default:
      return std::nullopt;
    }
  }

private:
  std::optional<NormalizedMessage> parse_quote(const RawPacket &packet,
                                               uint32_t seq) {
    if (packet.data.size() < 56)
      return std::nullopt;

    MarketDataUpdate update;
    update.source = Protocol::KALSHI_WS;
    update.sequence = seq;
    update.timestamp_ns = packet.recv_timestamp_ns;

    // Parse market_id (16 bytes string at offset 8)
    update.market_id =
        std::string(reinterpret_cast<const char *>(packet.data.data() + 8), 16);

    // Parse prices (doubles at offsets 24, 32, 40, 48)
    update.bid_price = ntoh_double(packet.data.data() + 24);
    update.ask_price = ntoh_double(packet.data.data() + 32);
    update.bid_size = ntoh_double(packet.data.data() + 40);
    update.ask_size = ntoh_double(packet.data.data() + 48);

    return update;
  }

  std::optional<NormalizedMessage> parse_trade(const RawPacket &packet,
                                               uint32_t seq) {
    if (packet.data.size() < 48)
      return std::nullopt;

    TradeEvent trade;
    trade.source = Protocol::KALSHI_WS;
    trade.timestamp_ns = packet.recv_timestamp_ns;

    trade.market_id =
        std::string(reinterpret_cast<const char *>(packet.data.data() + 8), 16);
    trade.trade_id = std::to_string(seq);
    trade.aggressor_side = (packet.data[24] == 0) ? Side::BUY : Side::SELL;
    trade.price = ntoh_double(packet.data.data() + 32);
    trade.size = ntoh_double(packet.data.data() + 40);

    return trade;
  }

  std::optional<NormalizedMessage> parse_book(const RawPacket &packet,
                                              uint32_t seq) {
    if (packet.data.size() < 32)
      return std::nullopt;

    OrderBookSnapshot book;
    book.source = Protocol::KALSHI_WS;
    book.sequence = seq;
    book.timestamp_ns = packet.recv_timestamp_ns;

    book.market_id =
        std::string(reinterpret_cast<const char *>(packet.data.data() + 8), 16);

    // Parse level count
    uint16_t bid_levels = ntoh16(packet.data.data() + 24);
    uint16_t ask_levels = ntoh16(packet.data.data() + 26);

    size_t offset = 28;

    // Parse bid levels (16 bytes each: price + size)
    for (uint16_t i = 0; i < bid_levels && offset + 16 <= packet.data.size();
         ++i) {
      BookLevel level;
      level.price = ntoh_double(packet.data.data() + offset);
      level.size = ntoh_double(packet.data.data() + offset + 8);
      level.timestamp_ns = packet.recv_timestamp_ns;
      book.bids.push_back(level);
      offset += 16;
    }

    // Parse ask levels
    for (uint16_t i = 0; i < ask_levels && offset + 16 <= packet.data.size();
         ++i) {
      BookLevel level;
      level.price = ntoh_double(packet.data.data() + offset);
      level.size = ntoh_double(packet.data.data() + offset + 8);
      level.timestamp_ns = packet.recv_timestamp_ns;
      book.asks.push_back(level);
      offset += 16;
    }

    return book;
  }
};

/**
 * Polymarket protocol parser
 */
class PolymarketParser : public ProtocolParser {
public:
  Protocol protocol() const override { return Protocol::POLYMARKET_WS; }

  std::optional<NormalizedMessage> parse(const RawPacket &packet) override {
    // Polymarket uses JSON over WebSocket
    // This would need JSON parsing (rapidjson or similar)
    return std::nullopt; // Placeholder
  }
};

/**
 * Packet normalizer that routes to appropriate parser
 */
class PacketNormalizer {
public:
  PacketNormalizer() {
    parsers_[Protocol::KALSHI_WS] = std::make_unique<KalshiParser>();
    parsers_[Protocol::POLYMARKET_WS] = std::make_unique<PolymarketParser>();
  }

  std::optional<NormalizedMessage> normalize(const RawPacket &packet) {
    auto it = parsers_.find(packet.protocol);
    if (it == parsers_.end()) {
      return std::nullopt;
    }
    return it->second->parse(packet);
  }

  void register_parser(std::unique_ptr<ProtocolParser> parser) {
    parsers_[parser->protocol()] = std::move(parser);
  }

private:
  std::unordered_map<Protocol, std::unique_ptr<ProtocolParser>> parsers_;
};

} // namespace quantshit
