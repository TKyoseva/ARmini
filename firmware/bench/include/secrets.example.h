// Copy to include/secrets.h (gitignored) and change the password. Used by the `remote` env (T12).
// WPA2 needs a password of at least 8 characters; the sketch refuses to start the AP otherwise.
#pragma once
#define AP_SSID "AR-Mini"
#define AP_PASS "change-me-8+chars"
