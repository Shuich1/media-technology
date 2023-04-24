import os
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QMainWindow, QMessageBox, QPushButton, QSlider,
                             QVBoxLayout, QWidget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hough Transform")

        screen_resolution = QApplication.desktop().screenGeometry()

        self.move(self.frameGeometry().width() // 2,
                  self.frameGeometry().height() // 2)

        self.left_label = QLabel()
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_label.setMinimumSize(
            screen_resolution.width() // 3, screen_resolution.width() // 4)
        self.left_label.setStyleSheet("border: 1px solid black;")

        self.right_label = QLabel()
        self.right_label.setAlignment(Qt.AlignCenter)
        self.right_label.setMinimumSize(
            screen_resolution.width() // 3, screen_resolution.width() // 4)
        self.right_label.setStyleSheet("border: 1px solid black;")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(500)
        self.slider.setTickInterval(5)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.update_slider)

        self.slider_label = QLabel()
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setText(f"Threshold: {self.slider.value()}")

        self.video_button = QPushButton("Start Video Stream")
        self.file_button = QPushButton("Upload File")
        self.save_button = QPushButton("Save image")
        self.save_button.setEnabled(False)

        self.video_button.clicked.connect(self.on_video_button)
        self.file_button.clicked.connect(self.upload_file)
        self.save_button.clicked.connect(self.save_image)
        self.is_camera_running = False

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.right_buttons_layout = QHBoxLayout()

        self.left_layout.addWidget(self.left_label)
        self.left_layout.addWidget(self.video_button)

        self.right_layout.addWidget(self.right_label)
        self.right_layout.addLayout(self.right_buttons_layout)

        self.right_buttons_layout.addWidget(self.file_button)
        self.right_buttons_layout.addWidget(self.save_button)

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.slider_label)
        self.main_layout.addWidget(self.slider)

        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.camera = cv2.VideoCapture(0)
        self.image_path = None

        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_camera)

    def on_video_button(self):
        if not self.camera:
            return

        if not self.is_camera_running:
            self.is_camera_running = True
            self.video_button.setText("Stop Video Stream")
            self.video_timer.start(15)
        else:
            self.is_camera_running = False
            self.video_button.setText("Start Video Stream")
            self.video_timer.stop()

    def hough_transform(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)
            threshold = self.slider.value()
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold)

            if lines is not None:
                for line in lines:
                    rho, theta = line[0]
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a*rho
                    y0 = b*rho
                    x1 = int(x0 + 1000*(-b))
                    y1 = int(y0 + 1000*(a))
                    x2 = int(x0 - 1000*(-b))
                    y2 = int(y0 - 1000*(a))
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            return frame

        except Exception as e:
            print("I cant process this image")
            return None

    def upload_file(self):
        self.image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.bmp *.tif *.jpeg *.hdr)")
        if self.image_path:
            QMessageBox.warning(
                self,
                "Warning",
                "The image shown in the program interface are resized. Use the Save Image Button to get the image in the original size."
            )
            self.update_image()
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def update_camera(self):
        try:
            _, frame = self.camera.read()
            frame = self.hough_transform(frame)
        except Exception as e:
            return

        if frame is None:
            return

        qimage = QImage(
            frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        self.left_label.setPixmap(pixmap)

    def update_image(self):
        try:
            frame = cv2.imread(self.image_path)
            frame = self.hough_transform(frame)
        except Exception as e:
            QMessageBox.critical(self, "Error", "Can`t process this image, maybe it`s too big or have incorrect file extension")
            return

        if frame is None:
            self.image_path = None
            return

        width = self.right_label.width()
        height = self.right_label.height()
        frame = cv2.resize(frame, (width, height))

        qimage = QImage(
            frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)

        self.right_label.setPixmap(pixmap)

    def save_image(self):
        directory_path = f'{os.path.dirname(os.path.realpath(__file__))}\images'

        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

        frame = cv2.imread(self.image_path)
        frame = self.hough_transform(frame)

        save_path = os.path.join(
            directory_path, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png")
        cv2.imwrite(save_path, frame)

    def update_slider(self):
        self.slider_label.setText(f"Threshold: {self.slider.value()}")
        if self.image_path:
            self.update_image()

    def closeEvent(self, event):
        self.video_timer.stop()
        self.camera.release()


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
