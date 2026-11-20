// DSI Recomp - achievements screen.
//
// Opened when the game asks the Xbox 360 dashboard for its achievements screen (the "Achievements"
// entry in the game's menus; see dsi_hooks.cpp). Names, descriptions and icons come from the game's
// own data in the current game language; unlocks come from the SDK's AchievementManager, which
// saves them automatically. The game is paused behind it (XN_SYS_UI) and gets no input until it
// closes.
//
// Controls: D-pad / left or right stick / mouse wheel scroll, LB/RB or LT/RT page,
// B, Back, Start, Esc or Backspace close. Keyboard players drive it through the keyboard mapping.

#pragma once

#include <rex/cvar.h>
#include <rex/input/input.h>
#include <rex/input/input_system.h>
#include <rex/runtime.h>
#include <rex/system/achievement_manager.h>
#include <rex/system/flags.h>
#include <rex/ui/imgui_dialog.h>
#include <rex/ui/imgui_drawer.h>
#include <rex/ui/immediate_drawer.h>
#include <rex/ui/overlay/achievement_icon_cache.h>
#include <imgui.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <string>
#include <vector>

#include "dsi_fonts.h"

REXCVAR_DECLARE(std::string, dsi_prompts);   // "xbox", "ps3" or "keyboard" (written by the launcher)

namespace dsi {

struct AchievementTexts {
  const char* title;
  const char* summary;     // printf: unlocked, total
  const char* locked;
  const char* unlocked_on; // printf: date
  const char* back;
  const char* none;
};

inline const AchievementTexts& TextsForLanguage(uint32_t xlang) {
  static const AchievementTexts en{"ACHIEVEMENTS", "%d of %d unlocked", "Locked", "Unlocked %s", "Back",
                                   "This game's achievement list could not be read."};
  static const AchievementTexts fr{"SUCCÈS", "%d sur %d débloqués", "Verrouillé", "Débloqué le %s", "Retour",
                                   "Impossible de lire la liste des succès du jeu."};
  static const AchievementTexts de{"ERFOLGE", "%d von %d freigeschaltet", "Gesperrt", "Freigeschaltet am %s",
                                   "Zurück", "Die Erfolgsliste des Spiels konnte nicht gelesen werden."};
  static const AchievementTexts es{"LOGROS", "%d de %d desbloqueados", "Bloqueado", "Desbloqueado el %s",
                                   "Volver", "No se pudo leer la lista de logros del juego."};
  static const AchievementTexts it{"OBIETTIVI", "%d di %d sbloccati", "Bloccato", "Sbloccato il %s",
                                   "Indietro", "Impossibile leggere l'elenco degli obiettivi del gioco."};
  switch (xlang) {   // rex::XLanguage values
    case 3: return de;
    case 4: return fr;
    case 5: return es;
    case 6: return it;
    default: return en;
  }
}

class AchievementsScreen : public rex::ui::ImGuiDialog {
 public:
  using Clock = std::chrono::steady_clock;

  // Dialogs own themselves: create with `new`; it deletes itself after Close().
  AchievementsScreen(rex::ui::ImGuiDrawer* imgui, rex::ui::ImmediateDrawer* immediate, rex::Runtime* runtime,
                     rex::system::AchievementManager* achievements, rex::input::InputSystem* input)
      : rex::ui::ImGuiDialog(imgui),
        achievements_(achievements),
        input_(input),
        icons_(immediate, runtime),
        texts_(TextsForLanguage(REXCVAR_GET(user_language))) {
    if (achievements_) list_ = achievements_->ListAchievements();
    prev_buttons_ = PadButtons(nullptr);   // ignore whatever is still held from opening the screen
    last_ = opened_ = Clock::now();
  }

 protected:
  void OnDraw(ImGuiIO& io) override {
    const auto now = Clock::now();
    const float dt = std::clamp(std::chrono::duration<float>(now - last_).count(), 0.0f, 0.1f);
    last_ = now;
    const float appear = std::clamp(std::chrono::duration<float>(now - opened_).count() / 0.15f, 0.0f, 1.0f);

    const ImVec2 ds = io.DisplaySize;
    const float s = std::max(0.6f, ds.y / 1080.0f);   // layout designed at 1080p

    // Full-screen dim layer that also keeps mouse clicks away from the game window.
    ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_Always);
    ImGui::SetNextWindowSize(ds, ImGuiCond_Always);
    ImGui::SetNextWindowBgAlpha(0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoSavedSettings | ImGuiWindowFlags_NoNav |
                                   ImGuiWindowFlags_NoBringToFrontOnFocus;
    if (ImGui::Begin("##dsi_achievements", nullptr, flags)) {
      ImDrawList* dl = ImGui::GetWindowDrawList();
      const float a = appear;
      dl->AddRectFilled(ImVec2(0, 0), ds, Col(0, 0, 0, 170, a));

      // Panel
      const float pw = std::min(ds.x - 40.0f * s, 1180.0f * s), ph = std::min(ds.y - 40.0f * s, 900.0f * s);
      const ImVec2 p0((ds.x - pw) * 0.5f, (ds.y - ph) * 0.5f + (1.0f - a) * 24.0f * s);
      const ImVec2 p1(p0.x + pw, p0.y + ph);
      dl->AddRectFilled(p0, p1, Col(11, 16, 23, 245, a), 10.0f * s);
      dl->AddRectFilled(p0, ImVec2(p1.x, p0.y + 128.0f * s), Col(20, 34, 50, 255, a), 10.0f * s,
                        ImDrawFlags_RoundCornersTop);
      dl->AddRect(p0, p1, Col(78, 128, 172, 255, a), 10.0f * s, 0, 2.0f * s);

      // Header: title, summary, gamerscore, progress bar
      int unlocked = 0, total_gs = 0, earned_gs = 0;
      for (const auto& e : list_) {
        total_gs += int(e.gamerscore);
        if (achievements_->IsUnlocked(e.id)) { ++unlocked; earned_gs += int(e.gamerscore); }
      }
      const float pad = 36.0f * s;
      Text(dl, Bold(), 46.0f * s, ImVec2(p0.x + pad, p0.y + 26.0f * s), Col(232, 241, 250, 255, a), texts_.title);
      char buf[160];
      std::snprintf(buf, sizeof(buf), texts_.summary, unlocked, int(list_.size()));
      Text(dl, Regular(), 24.0f * s, ImVec2(p0.x + pad, p0.y + 82.0f * s), Col(150, 176, 198, 255, a), buf);
      std::snprintf(buf, sizeof(buf), "%d / %d G", earned_gs, total_gs);
      TextRight(dl, Bold(), 30.0f * s, ImVec2(p1.x - pad, p0.y + 34.0f * s), Col(236, 196, 96, 255, a), buf);
      const float bar_y = p0.y + 116.0f * s, bar_w = pw - 2 * pad;
      dl->AddRectFilled(ImVec2(p0.x + pad, bar_y), ImVec2(p0.x + pad + bar_w, bar_y + 6.0f * s),
                        Col(38, 54, 70, 255, a), 3.0f * s);
      const float frac = list_.empty() ? 0.0f : float(unlocked) / float(list_.size());
      if (frac > 0)
        dl->AddRectFilled(ImVec2(p0.x + pad, bar_y), ImVec2(p0.x + pad + bar_w * frac, bar_y + 6.0f * s),
                          Col(86, 178, 236, 255, a), 3.0f * s);

      // List
      const ImVec2 l0(p0.x + pad, p0.y + 148.0f * s), l1(p1.x - pad, p1.y - 72.0f * s);
      const float row_h = 104.0f * s, gap = 10.0f * s, icon = 72.0f * s;
      const float content_h = list_.empty() ? 0.0f : list_.size() * (row_h + gap) - gap;
      const float view_h = l1.y - l0.y;
      const float max_scroll = std::max(0.0f, content_h - view_h);
      HandleInput(io, dt, row_h + gap, view_h);
      target_ = std::clamp(target_, 0.0f, max_scroll);
      scroll_ += (target_ - scroll_) * std::min(1.0f, dt * 14.0f);
      if (std::fabs(target_ - scroll_) < 0.5f) scroll_ = target_;

      dl->PushClipRect(l0, l1, true);
      if (list_.empty()) {
        Text(dl, Regular(), 24.0f * s, ImVec2(l0.x, l0.y + 20.0f * s), Col(170, 180, 190, 255, a), texts_.none);
      }
      for (size_t i = 0; i < list_.size(); ++i) {
        const float y = l0.y + i * (row_h + gap) - scroll_;
        if (y + row_h < l0.y || y > l1.y) continue;
        const auto& e = list_[i];
        const bool on = achievements_->IsUnlocked(e.id);
        const float rw = (max_scroll > 0 ? l1.x - 14.0f * s : l1.x);
        dl->AddRectFilled(ImVec2(l0.x, y), ImVec2(rw, y + row_h),
                          on ? Col(24, 46, 66, 255, a) : Col(17, 22, 29, 255, a), 6.0f * s);
        if (on) dl->AddRectFilled(ImVec2(l0.x, y), ImVec2(l0.x + 5.0f * s, y + row_h), Col(86, 178, 236, 255, a),
                                  6.0f * s, ImDrawFlags_RoundCornersLeft);
        // icon
        const ImVec2 i0(l0.x + 16.0f * s, y + (row_h - icon) * 0.5f);
        if (auto* tex = icons_.GetIcon(e)) {
          dl->AddImage(reinterpret_cast<ImTextureID>(tex), i0, ImVec2(i0.x + icon, i0.y + icon), ImVec2(0, 0),
                       ImVec2(1, 1), on ? Col(255, 255, 255, 255, a) : Col(255, 255, 255, 80, a));
        } else {
          dl->AddRectFilled(i0, ImVec2(i0.x + icon, i0.y + icon), Col(40, 52, 64, 255, a), 6.0f * s);
        }
        // text
        const float tx = i0.x + icon + 20.0f * s, right = rw - 20.0f * s;
        std::snprintf(buf, sizeof(buf), "%uG", e.gamerscore);
        const float gs_w = Bold()->CalcTextSizeA(26.0f * s, FLT_MAX, 0.0f, buf).x;
        TextRight(dl, Bold(), 26.0f * s, ImVec2(right, y + 18.0f * s),
                  on ? Col(236, 196, 96, 255, a) : Col(120, 124, 130, 255, a), buf);
        Text(dl, Bold(), 27.0f * s, ImVec2(tx, y + 16.0f * s),
             on ? Col(236, 244, 252, 255, a) : Col(160, 168, 178, 255, a), e.label.c_str(),
             right - tx - gs_w - 20.0f * s);
        const std::string& desc = on ? e.description : e.unachieved_description;
        Text(dl, Regular(), 21.0f * s, ImVec2(tx, y + 54.0f * s),
             on ? Col(168, 192, 212, 255, a) : Col(118, 126, 136, 255, a),
             desc.empty() ? e.description.c_str() : desc.c_str(), right - tx);
        if (on) {
          const std::string when = FormatDate(achievements_->GetUnlockTime(e.id));
          if (!when.empty()) {
            std::snprintf(buf, sizeof(buf), texts_.unlocked_on, when.c_str());
            TextRight(dl, Regular(), 18.0f * s, ImVec2(right, y + 58.0f * s), Col(120, 150, 176, 255, a), buf);
          }
        } else {
          TextRight(dl, Regular(), 18.0f * s, ImVec2(right, y + 58.0f * s), Col(110, 116, 124, 255, a),
                    texts_.locked);
        }
      }
      dl->PopClipRect();

      // Scrollbar
      if (max_scroll > 0) {
        const float x = l1.x - 6.0f * s, th = std::max(40.0f * s, view_h * view_h / content_h);
        const float ty = l0.y + (view_h - th) * (scroll_ / max_scroll);
        dl->AddRectFilled(ImVec2(x, l0.y), ImVec2(x + 6.0f * s, l1.y), Col(30, 40, 52, 255, a), 3.0f * s);
        dl->AddRectFilled(ImVec2(x, ty), ImVec2(x + 6.0f * s, ty + th), Col(86, 140, 186, 255, a), 3.0f * s);
      }

      // Footer: back prompt in the chosen button style
      DrawBackPrompt(dl, ImVec2(p1.x - pad, p1.y - 38.0f * s), s, a);
    }
    ImGui::End();
    ImGui::PopStyleVar(2);
  }

 private:
  static ImU32 Col(int r, int g, int b, int alpha, float fade) {
    return IM_COL32(r, g, b, int(alpha * fade));
  }

  static void Text(ImDrawList* dl, ImFont* f, float px, ImVec2 pos, ImU32 col, const char* t, float max_w = 0.0f) {
    if (max_w > 0.0f && f->CalcTextSizeA(px, FLT_MAX, 0.0f, t).x > max_w) {
      // single line, too long: wrap into the row instead of running under the gamerscore
      dl->AddText(f, px, pos, col, t, nullptr, max_w);
      return;
    }
    dl->AddText(f, px, pos, col, t);
  }
  static void TextRight(ImDrawList* dl, ImFont* f, float px, ImVec2 right_top, ImU32 col, const char* t) {
    const float w = f->CalcTextSizeA(px, FLT_MAX, 0.0f, t).x;
    dl->AddText(f, px, ImVec2(right_top.x - w, right_top.y), col, t);
  }

  static std::string FormatDate(uint64_t filetime) {
    if (filetime == 0) return {};
    const std::time_t t = std::time_t(filetime / 10000000ULL - 11644473600ULL);
    std::tm tm{};
#if defined(_WIN32)
    localtime_s(&tm, &t);
#else
    localtime_r(&t, &tm);
#endif
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d", &tm);
    return buf;
  }

  // Merged buttons of every connected pad (the keyboard mapping shows up as a pad too).
  uint32_t PadButtons(float* stick_y) {
    uint32_t buttons = 0;
    float best = 0.0f;
    if (input_) {
      for (uint32_t u = 0; u < 4; ++u) {
        rex::input::X_INPUT_STATE st{};
        if (input_->GetStateForUI(u, &st) != 0) continue;
        buttons |= uint32_t(uint16_t(st.gamepad.buttons));
        const float ly = float(int16_t(st.gamepad.thumb_ly)) / 32767.0f;
        const float ry = float(int16_t(st.gamepad.thumb_ry)) / 32767.0f;
        if (std::fabs(ly) > std::fabs(best)) best = ly;
        if (std::fabs(ry) > std::fabs(best)) best = ry;
        if (st.gamepad.left_trigger > 128) buttons |= kLeftTrigger;
        if (st.gamepad.right_trigger > 128) buttons |= kRightTrigger;
      }
    }
    if (stick_y) *stick_y = best;
    return buttons;
  }

  void HandleInput(ImGuiIO& io, float dt, float step, float page) {
    using namespace rex::input;
    float stick = 0.0f;
    const uint32_t now = PadButtons(&stick);
    const uint32_t pressed = now & ~prev_buttons_;
    prev_buttons_ = now;

    if ((pressed & (X_INPUT_GAMEPAD_B | X_INPUT_GAMEPAD_BACK | X_INPUT_GAMEPAD_START)) ||
        ImGui::IsKeyPressed(ImGuiKey_Escape, false)) {
      Close();
      return;
    }
    if (pressed & (X_INPUT_GAMEPAD_LEFT_SHOULDER | kLeftTrigger)) target_ -= page;
    if (pressed & (X_INPUT_GAMEPAD_RIGHT_SHOULDER | kRightTrigger)) target_ += page;

    // D-pad / stick: one row per press, then repeat while held
    int dir = 0;
    if (now & X_INPUT_GAMEPAD_DPAD_UP || stick > 0.5f) dir = -1;
    if (now & X_INPUT_GAMEPAD_DPAD_DOWN || stick < -0.5f) dir = 1;
    if (dir != 0) {
      if (dir != held_dir_) { target_ += dir * step; repeat_ = 0.35f; }
      else if ((repeat_ -= dt) <= 0.0f) { target_ += dir * step; repeat_ = 0.09f; }
    }
    held_dir_ = dir;

    if (io.MouseWheel != 0.0f) target_ -= io.MouseWheel * step;
  }

  void DrawBackPrompt(ImDrawList* dl, ImVec2 right_center, float s, float a) {
    const std::string& style = REXCVAR_GET(dsi_prompts);
    const float px = 24.0f * s;
    const float lw = Regular()->CalcTextSizeA(px, FLT_MAX, 0.0f, texts_.back).x;
    float x = right_center.x - lw;
    dl->AddText(Regular(), px, ImVec2(x, right_center.y - px * 0.55f), Col(200, 212, 224, 255, a), texts_.back);
    x -= 12.0f * s;
    const float r = 15.0f * s;
    if (style == "keyboard") {
      const char* k = "Esc";
      const float kw = Bold()->CalcTextSizeA(18.0f * s, FLT_MAX, 0.0f, k).x + 18.0f * s;
      dl->AddRectFilled(ImVec2(x - kw, right_center.y - r), ImVec2(x, right_center.y + r), Col(70, 92, 112, 255, a),
                        5.0f * s);
      dl->AddText(Bold(), 18.0f * s, ImVec2(x - kw + 9.0f * s, right_center.y - 10.0f * s), Col(236, 244, 252, 255, a),
                  k);
    } else if (style == "ps3") {
      const ImVec2 c(x - r, right_center.y);
      dl->AddCircleFilled(c, r, Col(52, 70, 92, 255, a), 32);
      dl->AddCircle(c, r * 0.55f, Col(236, 244, 252, 255, a), 32, 2.2f * s);   // PlayStation circle
    } else {
      const ImVec2 c(x - r, right_center.y);
      dl->AddCircleFilled(c, r, Col(196, 44, 40, 255, a), 32);                 // Xbox B
      const float bw = Bold()->CalcTextSizeA(20.0f * s, FLT_MAX, 0.0f, "B").x;
      dl->AddText(Bold(), 20.0f * s, ImVec2(c.x - bw * 0.5f, c.y - 11.0f * s), Col(255, 255, 255, 255, a), "B");
    }
  }

  // triggers are not buttons in X_INPUT_GAMEPAD; give them bits above the 16 button bits
  static constexpr uint32_t kLeftTrigger = 0x10000, kRightTrigger = 0x20000;
  rex::system::AchievementManager* achievements_;
  rex::input::InputSystem* input_;
  rex::ui::AchievementIconCache icons_;
  const AchievementTexts& texts_;
  std::vector<rex::system::AchievementInfo> list_;
  uint32_t prev_buttons_ = 0;
  int held_dir_ = 0;
  float repeat_ = 0.0f, scroll_ = 0.0f, target_ = 0.0f;
  Clock::time_point opened_, last_;
};

}  // namespace dsi
