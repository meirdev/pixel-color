import argparse
import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class PixelColor(QWidget):
    POLL_CURSOR_INTERVAL = 250
    PIXEL_COLOR_ALPHA = 200
    GRID_COLOR = QColor(255, 255, 255, 10)
    PIXEL_BORDER_COLOR = QColor(255, 0, 0, 120)

    def __init__(self, pixel_size: int, radius: int):
        super().__init__()

        self._pixel_size = pixel_size
        self._radius = radius

        self._current_color: QColor | None = None

        self._current_screen: QScreen = QApplication.screenAt(QCursor.pos())

        self.resize(self._current_screen.size())

        self._poll_cursor_timer = QTimer(self)
        self._poll_cursor_timer.setInterval(self.POLL_CURSOR_INTERVAL)
        self._poll_cursor_timer.timeout.connect(self._poll_cursor_slot)
        self._poll_cursor_timer.start()

        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.installEventFilter(self)
        self.setMouseTracking(True)
        self.show()

    def _poll_cursor_slot(self) -> None:
        current_screen = QApplication.screenAt(QCursor.pos())

        if current_screen != self._current_screen:
            # set the window in the new screen
            if current_screen is None:
                return
            self._current_screen = current_screen
            self.setGeometry(self._current_screen.geometry())
            self.resize(self._current_screen.size())

        pos = QCursor.pos()

        pixels_img = current_screen.grabWindow(
            0,
            x=pos.x() - self._radius // 2,
            y=pos.y() - self._radius // 2,
            width=self._radius * 2 + 1,
            height=self._radius * 2 + 1,
        ).toImage()

        self._current_color = pixels_img.pixelColor(self._radius, self._radius)

        width = height = self._radius * self._pixel_size * 2 + 1
        ps = self._pixel_size

        pixel_colors = QPixmap(width, height)
        pixel_colors.fill(Qt.GlobalColor.transparent)
        pixel_colors_painter = QPainter(pixel_colors)

        for x in range(pixels_img.width()):
            for y in range(pixels_img.height()):

                pixel_color = pixels_img.pixelColor(x, y)
                pixel_color.setAlpha(self.PIXEL_COLOR_ALPHA)
                pixel_colors_painter.fillRect(x * ps, y * ps, ps, ps, pixel_color)

                pixel_colors_painter.setPen(self.GRID_COLOR)
                pixel_colors_painter.drawLine(x * ps, y * ps, x * ps + ps, y * ps)
                pixel_colors_painter.drawLine(x * ps, y * ps, x * ps, y * ps + ps)

        pixel_colors_painter.setPen(self.PIXEL_BORDER_COLOR)
        pixel_colors_painter.drawRect(self._radius * ps, self._radius * ps, ps, ps)
        pixel_colors_painter.end()

        # +2 for the border
        ellipse_mask = QPixmap(width + 2, height + 2)
        ellipse_mask.fill(Qt.GlobalColor.transparent)

        ellipse_mask_brush = QBrush(pixel_colors)
        ellipse_mask_painter = QPainter(ellipse_mask)
        ellipse_mask_painter.setBrush(ellipse_mask_brush)
        ellipse_mask_painter.setPen(Qt.GlobalColor.gray)
        ellipse_mask_painter.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform,
            True,
        )
        ellipse_mask_painter.drawEllipse(1, 1, width, height)
        ellipse_mask_painter.end()

        QApplication.changeOverrideCursor(QCursor(ellipse_mask))

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if (
                event.key() == Qt.Key.Key_C
                and event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                QApplication.clipboard().setText(self._current_color.name())
            elif event.key() == Qt.Key.Key_Escape:
                self.close()
        return False


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        "Pixel Color",
        usage="""%(prog)s [options]
    
    Press Ctrl+C to copy the color to the clipboard.
    Press Escape to exit.
    """,
    )
    arg_parser.add_argument(
        "-p", "--pixel-size", type=int, default=4, help="Size of each pixel"
    )
    arg_parser.add_argument(
        "-r", "--radius", type=int, default=20, help="Radius of the pixel grid"
    )

    args = arg_parser.parse_args()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(".icon.ico"))

    window = PixelColor(pixel_size=args.pixel_size, radius=args.radius)
    app.exec()
