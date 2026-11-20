// DSI Recomp - Killers' Heaven boot splash.
//
// Shown before the game module is launched (DsignitionApp::LaunchModule), so the game's own
// EA / Visceral intro still plays afterwards. Black screen, logo, fade in/out, ~3 s total.
// Any key, mouse button or gamepad button skips it. The logo is loaded from
// branding/killers_heaven_on_dark.png next to the exe (the working directory set by the launchers).

#pragma once

#include <rex/ui/image_decode.h>
#include <rex/ui/imgui_dialog.h>
#include <rex/ui/imgui_drawer.h>
#include <rex/ui/immediate_drawer.h>
#include <imgui.h>

#include "dsi_fonts.h"

#include <algorithm>
#include <chrono>
#include <fstream>
#include <functional>
#include <iterator>
#include <memory>
#include <string>
#include <vector>

class SplashDialog : public rex::ui::ImGuiDialog {
 public:
  using Clock = std::chrono::steady_clock;

  // Dialogs own themselves: create with `new`; it deletes itself after Close().
  SplashDialog(rex::ui::ImGuiDrawer* imgui, rex::ui::ImmediateDrawer* immediate,
               const std::string& logo_path, std::function<void()> on_done)
      : rex::ui::ImGuiDialog(imgui), on_done_(std::move(on_done)) {
    std::ifstream f(logo_path, std::ios::binary);
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (!bytes.empty() && immediate) {
      int w = 0, h = 0;
      auto rgba = rex::ui::DecodeImageRGBA(bytes.data(), bytes.size(), w, h);
      if (!rgba.empty()) {
        logo_ = immediate->CreateTexture(uint32_t(w), uint32_t(h), rex::ui::ImmediateTextureFilter::kLinear,
                                         false, rgba.data());
        logo_w_ = float(w);
        logo_h_ = float(h);
      }
    }
    start_ = Clock::now();
  }

 protected:
  void OnDraw(ImGuiIO& io) override {
    if (done_) return;
    const float t = std::chrono::duration<float>(Clock::now() - start_).count();
    bool skip = t > 0.3f && (ImGui::IsAnyItemActive() || AnyInput(io));
    if (t >= kTotal || skip) {
      Finish();
      return;
    }
    float alpha = 1.0f;
    if (t < kFadeIn) alpha = t / kFadeIn;
    else if (t > kTotal - kFadeOut) alpha = (kTotal - t) / kFadeOut;
    alpha = std::clamp(alpha, 0.0f, 1.0f);

    const ImVec2 size = io.DisplaySize;
    ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_Always);
    ImGui::SetNextWindowSize(size, ImGuiCond_Always);
    ImGui::SetNextWindowBgAlpha(1.0f);   // stays opaque: the game has not started yet
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::PushStyleColor(ImGuiCol_WindowBg, IM_COL32(0, 0, 0, 255));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings | ImGuiWindowFlags_NoFocusOnAppearing |
                                   ImGuiWindowFlags_NoNav;
    if (ImGui::Begin("##kh_splash", nullptr, flags)) {
      ImDrawList* dl = ImGui::GetWindowDrawList();
      const ImU32 a8 = ImU32(alpha * 255.0f) << IM_COL32_A_SHIFT;
      float cy = size.y * 0.46f;
      if (logo_) {
        float w = size.x * 0.46f, h = w * logo_h_ / logo_w_;
        ImVec2 p0((size.x - w) * 0.5f, cy - h * 0.5f);
        dl->AddImage(reinterpret_cast<ImTextureID>(logo_.get()), p0, ImVec2(p0.x + w, p0.y + h),
                     ImVec2(0, 0), ImVec2(1, 1), IM_COL32(255, 255, 255, 0) | a8);
        cy += h * 0.5f;
      }
      const float scale = std::max(1.0f, size.y / 720.0f);
      // DejaVu Sans when fonts\ is present (has the \u2122 and \u00A9 signs), else the SDK pixel font
      const bool nice = dsi::g_font_regular != nullptr;
      CenterText(dl, nice ? "DSI Recomp  \u2013  native PC recompilation" : "DSI Recomp  -  native PC recompilation",
                 cy + 30.0f * scale,
                 (nice ? 22.0f : 20.0f) * scale, IM_COL32(180, 190, 200, 0) | a8, size.x);
      CenterText(dl, nice ? "Dead Space\u2122 Ignition \u00A9 2010 Electronic Arts Inc."
                          : "Dead Space(TM) Ignition (C) 2010 Electronic Arts Inc.",
                 size.y - 64.0f * scale, 15.0f * scale, IM_COL32(120, 128, 138, 0) | a8, size.x);
      CenterText(dl, "Unofficial fan project. Not affiliated with or endorsed by Electronic Arts.",
                 size.y - 40.0f * scale, 15.0f * scale, IM_COL32(120, 128, 138, 0) | a8, size.x);
    }
    ImGui::End();
    ImGui::PopStyleColor();
    ImGui::PopStyleVar(2);
  }

 private:
  static constexpr float kFadeIn = 0.45f, kTotal = 3.0f, kFadeOut = 0.5f;

  static bool AnyInput(ImGuiIO& io) {
    if (ImGui::IsMouseClicked(ImGuiMouseButton_Left) || ImGui::IsMouseClicked(ImGuiMouseButton_Right)) return true;
    for (int k = ImGuiKey_NamedKey_BEGIN; k < ImGuiKey_NamedKey_END; ++k) {
      if (ImGui::IsKeyPressed(ImGuiKey(k), false)) return true;
    }
    (void)io;
    return false;
  }

  // px = text height in pixels
  static void CenterText(ImDrawList* dl, const char* text, float y, float px, ImU32 col, float width) {
    ImFont* font = dsi::Regular();
    ImVec2 ts = font->CalcTextSizeA(px, FLT_MAX, 0.0f, text);
    dl->AddText(font, px, ImVec2((width - ts.x) * 0.5f, y), col, text);
  }

  void Finish() {
    done_ = true;
    if (on_done_) on_done_();
    Close();
  }

  std::function<void()> on_done_;
  std::unique_ptr<rex::ui::ImmediateTexture> logo_;
  float logo_w_ = 1.0f, logo_h_ = 1.0f;
  Clock::time_point start_;
  bool done_ = false;
};
