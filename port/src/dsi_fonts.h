// DSI Recomp - fonts for our own screens (splash, achievements).
//
// The SDK's default ImGui font is a 10 px pixel font with Latin-1 only. DsignitionApp::OnConfigureFonts
// adds DejaVu Sans (regular + bold, from fonts\ next to the exe) at a large size so text stays sharp
// when drawn smaller, with Latin-1 plus the typographic marks the game's languages and our credits use
// (™, ©, dashes, quotes, ellipsis). The SDK font stays the default, so its own overlays are unchanged.
// When the font files are missing, both pointers stay null and callers fall back to the default font.

#pragma once

#include <imgui.h>

#include <filesystem>
#include <string>

namespace dsi {

inline ImFont* g_font_regular = nullptr;
inline ImFont* g_font_bold = nullptr;
constexpr float kFontBakeSize = 48.0f;   // baked size; drawn at any smaller size

inline void LoadFonts(ImFontAtlas* atlas, const std::filesystem::path& dir) {
  static const ImWchar ranges[] = {
      0x0020, 0x00FF,   // Basic Latin + Latin-1 (French, German, Italian, Spanish)
      0x0152, 0x0153,   // Œ œ
      0x2013, 0x2026,   // – — ‘ ’ “ ” … and friends
      0x2122, 0x2122,   // ™
      0,
  };
  ImFontConfig cfg;
  cfg.OversampleH = 2;
  cfg.OversampleV = 1;
  const auto regular = dir / "DejaVuSans.ttf";
  const auto bold = dir / "DejaVuSans-Bold.ttf";
  std::error_code ec;
  if (std::filesystem::exists(regular, ec)) {
    g_font_regular = atlas->AddFontFromFileTTF(regular.string().c_str(), kFontBakeSize, &cfg, ranges);
  }
  if (std::filesystem::exists(bold, ec)) {
    g_font_bold = atlas->AddFontFromFileTTF(bold.string().c_str(), kFontBakeSize, &cfg, ranges);
  }
  if (!g_font_bold) g_font_bold = g_font_regular;
}

// Font to draw with: ours if loaded, else the current ImGui font.
inline ImFont* Regular() { return g_font_regular ? g_font_regular : ImGui::GetFont(); }
inline ImFont* Bold() { return g_font_bold ? g_font_bold : ImGui::GetFont(); }

}  // namespace dsi
