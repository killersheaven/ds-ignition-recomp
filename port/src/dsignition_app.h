// dsignition - ReXGlue Recompiled Project
//
// Customize your app by overriding virtual hooks from rex::ReXApp.

#pragma once

#include <rex/rex_app.h>

#include <filesystem>

#include "splash_dialog.h"

class DsignitionApp : public rex::ReXApp {
 public:
  using rex::ReXApp::ReXApp;

  static std::unique_ptr<rex::ui::WindowedApp> Create(
      rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<DsignitionApp>(new DsignitionApp(ctx, "dsignition",
        PPCImageConfig));
  }

  // Override virtual hooks for customization:
  // void OnPostInitLogging() override {}
  // void OnPreSetup(rex::RuntimeConfig& config) override {}
  // void OnLoadXexImage(std::string& xex_image) override {}
  // void OnPostLoadXexImage() override {}
  // void OnPostSetup() override {}
  // void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override {}
  // std::unique_ptr<rex::ui::ImGuiDialog> CreateAchievementsOverlay() override;
  // std::unique_ptr<rex::ui::AchievementNotificationDialog>
  // CreateAchievementNotificationDialog() override;
  // void OnShutdown() override {}
  // void OnConfigurePaths(rex::PathConfig& paths) override {}

 protected:
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
  bool splash_shown_ = false;
};
