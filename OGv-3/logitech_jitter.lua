-- Logitech G HUB Lua Jitter Script
-- Requirements: Logitech G HUB must be installed.
-- Instructions:
-- 1. Open Logitech G HUB.
-- 2. Click on your Active Profile for the game at the top widget.
-- 3. Click the 'Scripting' icon (looks like { }) at the bottom.
-- 4. Delete the default code, paste this code, and click "Script -> Save" (Ctrl+S).
-- 5. It will now run directly through your Logitech mouse hardware in any 3D game.

function OnEvent(event, arg)
    -- Button 1 is Left Click, Button 3 is Right Click (Button 2 is usually Middle Click)
    if event == "MOUSE_BUTTON_PRESSED" and (arg == 1 or arg == 3) then
        if IsMouseButtonPressed(1) and IsMouseButtonPressed(3) then
            while IsMouseButtonPressed(1) and IsMouseButtonPressed(3) do
                MoveMouseRelative(-3, 0)
                Sleep(5)
                MoveMouseRelative(3, 0)
                Sleep(5)
            end
        end
    end
end
