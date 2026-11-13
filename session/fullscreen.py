"""The writing window, filling the screen or sitting in its frame."""


class FullscreenControl:
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        # Call showFullScreen/showNormal on the parent QMainWindow
        if self.is_fullscreen:
            self.parent().showFullScreen()
        else:
            self.parent().showNormal()
        self.fullscreen_btn.setText("Minimize" if self.is_fullscreen else "Fullscreen")

    

