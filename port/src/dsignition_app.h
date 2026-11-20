// dsignition - ReXGlue Recompiled Project
//
// Customize your app by overriding virtual hooks from rex::ReXApp.

#pragma once

#include <rex/filesystem.h>
#include <rex/input/input_system.h>
#include <rex/rex_app.h>
#include <rex/runtime.h>
#include <rex/system/kernel_state.h>
#include <rex/thread.h>

#include <chrono>
#include <filesystem>

#include "achievements_screen.h"
#include "dsi_fonts.h"
#include "splash_dialog.h"

class DsignitionApp : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(
      rex::ui::WindowedAppContext& ctx) {
    auto app = std::unique_ptr<DsignitionApp>(new DsignitionApp(ctx, "dsignition",
        PPCImageConfig));
    instance_ = app.get();
    return app;
  }

  // DSI Recomp: the game's "Achievements" menu entry (dsi_hooks.cpp). Runs on the game thread
  // that asked for it and returns when the player closes the screen, like the Xbox 360 dashboard
  // did: the game gets XN_SYS_UI (pauses) and no input while it is open.
  static void ShowAchievementsBlocking() {
    DsignitionApp* app = instance_;
    auto* ks = REX_KERNEL_STATE();
    if (!app || !ks || !ks->emulator()) return;
    rex::Runtime* rt = ks->emulator();
    if (!rt->app_context() || !app->imgui_drawer() || !app->immediate_drawer()) return;
    auto* input = static_cast<rex::input::InputSystem*>(rt->input_system());

    ks->BroadcastNotification(0x9, 1);   // XN_SYS_UI = true
    if (input) input->AddUIInputBlocker();
    rex::thread::Fence fence;
    bool shown = false;
    rt->app_context()->CallInUIThreadSynchronous([&]() {
      auto* screen = new dsi::AchievementsScreen(app->imgui_drawer(), app->immediate_drawer(), rt,
                                                 &ks->achievements(), input);
      screen->Then(&fence);   // signalled when the screen deletes itself
      shown = true;
    });
    if (shown) fence.Wait();
    if (input) input->RemoveUIInputBlocker();
    rex::thread::Sleep(std::chrono::milliseconds(100));
    ks->BroadcastNotification(0x9, 0);   // XN_SYS_UI = false
  }

 protected:
  // DSI Recomp: DejaVu Sans for our own screens (fonts\ next to the exe; see dsi_fonts.h).
  void OnConfigureFonts(ImFontAtlas* atlas) override {
    dsi::LoadFonts(atlas, rex::filesystem::GetExecutableFolder() / "fonts");
  }

  // DSI Recomp: show the Killers' Heaven splash first, then start the game when it finishes,
  // so the game's own EA / Visceral intro is not covered.
  void LaunchModule() override {
    static const char* kLogo = "branding/killers_heaven_on_dark.png";
    if (splash_shown_ || !imgui_drawer() || !immediate_drawer() || !std::filesystem::exists(kLogo)) {
      splash_shown_ = true;
      rex::ReXApp::LaunchModule();
      return;
    }
    splash_shown_ = true;
    app_context().CallInUIThreadDeferred([this]() {
      new SplashDialog(imgui_drawer(), immediate_drawer(), kLogo, [this]() {
        app_context().CallInUIThreadDeferred([this]() { rex::ReXApp::LaunchModule(); });
      });
    });
  }

 private:
  static inline DsignitionApp* instance_ = nullptr;
  bool splash_shown_ = false;
};
