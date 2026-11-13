"""The fifteen-minute countdown the clock shows."""


class TimerControl:
    def toggle_timer(self):
        self.timer_is_running = not self.timer_is_running
        # Stopping rests at 15:00. Starting from zero begins a fresh fifteen minutes.
        if not self.timer_is_running or self.time_remaining <= 0: self.time_remaining = 900
        self.update_timer_button()
        self._return_to_page(self.clock)

    def update_timer(self):
        if self.timer_is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_timer_button()
            return
        if self.timer_is_running and self.time_remaining <= 0:
            self.timer_is_running = False
            self.bottom_nav_opacity = 1.0
            self.update_timer_button()

    def update_timer_button(self):
        self.clock.show_time(self.time_remaining, self.timer_is_running)
