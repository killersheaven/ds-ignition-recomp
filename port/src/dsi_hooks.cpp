// DSI Recomp - replacements for game functions, and our own settings.
//
// Every recompiled game function is a weak symbol, so defining one here with the same name
// replaces it (see DEFINE_REX_FUNC in generated/default/dsignition_pch.h).

#include "generated/default/dsignition_init.h"

#include <rex/cvar.h>
#include <rex/hook.h>

#include "dsignition_app.h"

// Which button prompts the launcher installed ("xbox", "ps3", "keyboard"). Only used to draw
// the matching Back button on our own screens; written to dsignition.toml by the launcher.
REXCVAR_DEFINE_STRING(dsi_prompts, "xbox", "DSI", "Button prompt style for DSI Recomp screens: xbox, ps3, keyboard");

// sub_8214A5B0: the game's "show achievements" call. On the Xbox 360 it was
//     li r4, 0 ; b XamShowAchievementsUI
// and opened the dashboard's achievements screen, which ReXGlue leaves as a stub.
// It now opens our achievements screen and returns ERROR_SUCCESS once it is closed.
REX_HOOK_RAW(sub_8214A5B0) {
  (void)base;
  DsignitionApp::ShowAchievementsBlocking();
  ctx.r3.u64 = 0;
}
