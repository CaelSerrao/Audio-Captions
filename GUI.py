import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QProgressBar, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from predict2 import generate_srt, mux_subtitles
from final_step import audio_to_video_with_subs
import os
import shutil
import subprocess

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4a", ".wav"}

class Worker(QObject):
    progress = Signal(int)
    message = Signal(str)
    finished = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        self.progress.emit(10)
        self.message.emit("Transcribing...")

        srt_path = generate_srt(self.path)

        self.progress.emit(70)
        self.message.emit("Muxing subtitles...")
        if self.path.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
            new_video = mux_subtitles(self.path, srt_path)
        else:
            new_video = audio_to_video_with_subs("static/audio_icon.jpg", self.path, srt_path)

        self.progress.emit(100)
        self.message.emit("Done!")

        self.finished.emit(new_video)


class DropArea(QListWidget):
    fileReady = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

        self.setStyleSheet("""
            QListWidget {
                border: 3px dashed #888;
                font-size: 16px;
                padding: 20px;
            }
        """)

        self.addItem("Drag & Drop videos here")


    def start_processing(self, path):
        self.thread = QThread()
        self.worker = Worker(path)

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.message.connect(self.addItem)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.fileReady)

        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()


    def update_progress(self, value):
        self.parent().progress.setValue(value)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.clear()

        for url in event.mimeData().urls():
            path = url.toLocalFile()

            if any(path.lower().endswith(ext) for ext in VIDEO_EXTS):
                self.addItem(path)
                self.start_processing(path)


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Offline Video Caption Tool")
        self.resize(600, 450)

        layout = QVBoxLayout()

        label = QLabel("Drop your video files below")
        label.setAlignment(Qt.AlignCenter)

        self.drop = DropArea()

        # ⭐ progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)

        # ⭐ open button

        layout.addWidget(label)
        layout.addWidget(self.drop)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        self.drop.fileReady.connect(self.file_ready)


    def file_ready(self, path):
        self.output_path = path
        self.save_video(path)


    def open_file(self):
        subprocess.run(["open", self.output_path])  # macOS
    from PySide6.QtWidgets import QFileDialog

    def save_video(self, video_path):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", video_path, "MP4 Video (*.mp4)"
        )
        if save_path:
            shutil.copy(video_path, save_path)
            self.drop.addItem(f"Saved to: {save_path}")





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
