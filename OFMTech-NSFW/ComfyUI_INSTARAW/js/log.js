// --------------------------------------------------------------------------
// Portions of this file are derived from cg-image-filter
//   https://github.com/chrisgoringe/cg-image-filter
//   Copyright 2024-2025 Chris Goringe
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.
//
// NOTICE: This file has been modified from the cg-image-filter original. The
// logging setting key was changed from "Image Filter.Z.Detailed Logging" to
// "INSTARAW.Interactive.DetailedLogging".
//
// Full third-party attribution for this package is in
// ../THIRD_PARTY_NOTICES.md (package root). Licence text:
// ../licenses/Apache-2.0.txt
// --------------------------------------------------------------------------

// ---
// Filename: ../ComfyUI_INSTARAW/js/log.js
// ---

import { app } from "../../scripts/app.js";

export class Log {
    static log(s) { if (s) console.log(s) }
    static error(e) { console.error(e) }
    static detail(s) {
        // Updated settings key
        if (app.ui.settings.getSettingValue("INSTARAW.Interactive.DetailedLogging")) Log.log(s)
    }
    static message_in(message, extra) {
        // Updated settings key
        if (!app.ui.settings.getSettingValue("INSTARAW.Interactive.DetailedLogging")) return
        if (message.detail && !message.detail.tick) Log.log(`--> ${JSON.stringify(message.detail)}` + (extra ? ` ${extra}` : ""))
        if (message.detail && message.detail.tick) Log.log(`--> tick`)
    }
    static message_out(response, extra) {
        // Updated settings key
        if (!app.ui.settings.getSettingValue("INSTARAW.Interactive.DetailedLogging")) return
        Log.log(`"<-- ${JSON.stringify(response)}` + (extra ? ` ${extra}` : ""))
    }
}