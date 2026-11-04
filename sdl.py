from nxbt.nxbt import Nxbt, PRO_CONTROLLER, DIRECT_INPUT_PACKET
import sdl3
import sys
import ctypes

class Sdl:
    def __init__(
        self,
    ):
        if not sdl3.SDL_Init(sdl3.SDL_INIT_GAMEPAD):
            print("SDL Init failed: {sdl3.SDL_GetError().decode()}", file=sys.stderr)
        self.opened_gamepads = {}
        self.running = True
        self.nx = Nxbt()
        self.input_packet = self.nx.create_input_packet()
        self.controller_index = -1

    def __del__(self):
        sdl3.SDL_Quit()

    def start(self):
        self.mainloop()

    def mainloop(self):
        self.controller_index = self.nx.create_controller(PRO_CONTROLLER)
        print("Waiting for switch to connect. Please turn on your Switch and navigate to the 'Change Grip/Order menu.")
        self.nx.wait_for_connection(self.controller_index)
        event = sdl3.SDL_Event()
        while self.running:
            # Poll all events from the SDL3 queue
            while sdl3.SDL_PollEvent(ctypes.byref(event)):
                match event.type:
                    case sdl3.SDL_EVENT_QUIT:
                        self.running = False
                    case sdl3.SDL_EVENT_GAMEPAD_ADDED:
                        # event.gdevice.which contains the instance ID in SDL3
                        instance_id = event.gdevice.which
                        gamepad_ptr = sdl3.SDL_OpenGamepad(instance_id)
                        if gamepad_ptr:
                            self.opened_gamepads[instance_id] = gamepad_ptr
                            name = sdl3.SDL_GetGamepadName(gamepad_ptr).decode('utf-8')
                            print(f"🎮 Gamepad Connected: {name} (ID: {instance_id})")
                    case sdl3.SDL_EVENT_GAMEPAD_REMOVED:
                        instance_id = event.gdevice.which
                        if instance_id in self.opened_gamepads:
                            sdl3.SDL_CloseGamepad(self.opened_gamepads[instance_id])
                            del self.opened_gamepads[instance_id]
                            print(f"❌ Gamepad Disconnected (ID: {instance_id})")
                    # --- Gamepad Button Events ---
                    case sdl3.SDL_EVENT_GAMEPAD_BUTTON_DOWN | sdl3.SDL_EVENT_GAMEPAD_BUTTON_UP:
                        instance_id = event.gbutton.which
                        button_id = event.gbutton.button
                        is_pressed = event.gbutton.down
                        self.handle_gamepad_button(button_id, is_pressed)

                    # --- Gamepad Axis Events (Thumbsticks & Triggers) ---
                    case sdl3.SDL_EVENT_GAMEPAD_AXIS_MOTION:
                        instance_id = event.gaxis.which
                        axis_id = event.gaxis.axis
                        raw_value = event.gaxis.value # Range: -32768 to 32767
                        self.handle_gamepad_axis(axis_id, raw_value)


    def handle_gamepad_button(self, button_id: sdl3.SDL_GamepadButton, is_pressed: bool):
        match button_id:
            case sdl3.SDL_GAMEPAD_BUTTON_SOUTH:
                self.input_packet["B"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_EAST:
                self.input_packet["A"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_WEST:
                self.input_packet["Y"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_NORTH:
                self.input_packet["X"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_BACK:
                self.input_packet["MINUS"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_START:
                self.input_packet["PLUS"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_DPAD_UP:
                self.input_packet["DPAD_UP"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_DPAD_LEFT:
                self.input_packet["DPAD_LEFT"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_DPAD_RIGHT:
                self.input_packet["DPAD_RIGHT"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_DPAD_DOWN:
                self.input_packet["DPAD_DOWN"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_GUIDE:
                self.input_packet["HOME"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_LEFT_SHOULDER:
                self.input_packet["L"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER:
                self.input_packet["R"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_LEFT_STICK:
                self.input_packet["L_STICK"]["PRESSED"] = is_pressed
            case sdl3.SDL_GAMEPAD_BUTTON_RIGHT_STICK:
                self.input_packet["R_STICK"]["PRESSED"] = is_pressed
        self.nx.set_controller_input(self.controller_index, self.input_packet)

    def handle_gamepad_axis(self, axis_id: sdl3.SDL_GamepadAxis, raw_value):
        # Normalize trigger/stick values between -100.0 and 100.0 (or 0.0 to 100.0 for triggers)
        normalized = (raw_value*100) / 32767.0 if raw_value >= 0 else (raw_value*100) / 32768.0
        match axis_id:
            case sdl3.SDL_GAMEPAD_AXIS_LEFT_TRIGGER:
                if normalized > 0:
                    self.input_packet["ZL"] = True
                else:
                    self.input_packet["ZL"] = False
            case sdl3.SDL_GAMEPAD_AXIS_RIGHT_TRIGGER:
                if normalized > 0:
                    self.input_packet["ZR"] = True
                else:
                    self.input_packet["ZR"] = False
            case sdl3.SDL_GAMEPAD_AXIS_LEFTX:
                self.input_packet["L_STICK"]["X_VALUE"] = normalized
            case sdl3.SDL_GAMEPAD_AXIS_LEFTY:
                self.input_packet["L_STICK"]["Y_VALUE"] = -normalized
            case sdl3.SDL_GAMEPAD_AXIS_RIGHTX:
                self.input_packet["R_STICK"]["X_VALUE"] = normalized
            case sdl3.SDL_GAMEPAD_AXIS_RIGHTY:
                self.input_packet["R_STICK"]["Y_VALUE"] = -normalized
        self.nx.set_controller_input(self.controller_index, self.input_packet)

if __name__ == "__main__":
    try:
        sdl = Sdl()
        sdl.start()
    except KeyboardInterrupt:
        exit()
