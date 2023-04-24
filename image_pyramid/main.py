import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                             QPushButton, QSlider, QVBoxLayout, QWidget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Pyramid")
        
        self.move(self.frameGeometry().width() // 2,
                  self.frameGeometry().height() // 2)

        self.image_button = QPushButton("Upload Image")
        self.image_button.clicked.connect(self.upload_image)
        self.save_images_button = QPushButton("Save Images")
        self.save_images_button.clicked.connect(self.save_images)
        self.save_images_button.setEnabled(False)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(2)
        self.slider.setMaximum(9)
        self.slider.setTickInterval(1)
        self.slider.setValue(3)
        self.slider.valueChanged.connect(self.update_slider)

        self.slider_label = QLabel()
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setText(f"Pyramid levels: {self.slider.value()}")

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.layout = QHBoxLayout()
        self.left_layout = QGridLayout()
        self.right_layout = QGridLayout()

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.image_button)
        self.main_layout.addWidget(self.save_images_button)
        self.main_layout.addWidget(self.slider_label)
        self.main_layout.addWidget(self.slider)

        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.image_path = None
        self.gaussian_pyramid_images = []
        self.laplacian_pyramid_images = []

    def update_slider(self):
        self.slider_label.setText(f"Pyramid levels: {self.slider.value()}")
        self.update_images()

    def upload_image(self):
        self.image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg)")
        if self.image_path:
            QMessageBox.warning(
                self,
                "Warning",
                "The images shown in the program interface are resized. Use the Save Images Button to get the images in their original size."
            )
            self.save_images_button.setEnabled(True)
        else:
            self.save_images_button.setEnabled(False)

        self.update_images()

    def update_images(self):
        self.clear_layouts()
        self.gaussian_pyramid_images = []
        self.laplacian_pyramid_images = []

        if self.image_path:
            try:
                image = cv2.imread(self.image_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", "Can`t process this image, maybe it`s too big or have incorrect file extension")
                return

            self.gaussian_pyramid_images = self.gaussian_pyramid(image)
            for idx, img in enumerate(self.gaussian_pyramid_images):
                label = QLabel()
                label.setFixedSize(256, 256)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("border: 1px solid black;")

                img = cv2.resize(img, (label.width(), label.height()))

                qimage = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(qimage)


                label.setPixmap(pixmap)

                self.left_layout.addWidget(label, idx % 3, idx // 3)
            
            self.laplacian_pyramid_images = self.laplacian_pyramid(self.gaussian_pyramid_images)
            for idx, img in enumerate(self.laplacian_pyramid_images):
                label = QLabel()
                label.setFixedSize(256, 256)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("border: 1px solid black;")

                img = cv2.resize(img, (label.width(), label.height()))

                qimage = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(qimage)


                label.setPixmap(pixmap)

                self.right_layout.addWidget(label, idx % 3, idx // 3)

    def save_images(self):
        image_name = self.image_path.split('/')[-1].split(".")[0]
        
        directory_path = f'{os.path.dirname(os.path.realpath(__file__))}\images\{image_name}'

        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

        for idx, img in enumerate(self.gaussian_pyramid_images):
            save_path = os.path.join(
                directory_path, f"{image_name}_gaussian_{idx}.png"
            )
            cv2.imwrite(save_path, img)

        for idx, img in enumerate(self.laplacian_pyramid_images):
            save_path = os.path.join(
                directory_path, f"{image_name}_laplasian_{idx}.png"
            )
            cv2.imwrite(save_path, img)
    
    def gaussian_pyramid(self, image):
        tmp_img = image.copy()
        pyramid = []
        for i in range(self.slider.value()):
            new_img = cv2.pyrDown(tmp_img)
            pyramid.append(new_img)
            tmp_img = new_img.copy()
        
        return pyramid
    
    def laplacian_pyramid(self, gaussian_pyramid):
        pyramid = []
        for i in range(len(gaussian_pyramid) - 1, 0, -1):
            gaussian_expanded = cv2.pyrUp(gaussian_pyramid[i])
            height, width = gaussian_pyramid[i - 1].shape[:2]
            laplacian = cv2.subtract(gaussian_pyramid[i - 1], cv2.resize(gaussian_expanded, (width, height)))
            pyramid.append(laplacian)

        pyramid.append(gaussian_pyramid[0])
        return pyramid

    def clear_layouts(self):
        for i in reversed(range(self.left_layout.count())): 
            self.left_layout.itemAt(i).widget().setParent(None)
        
        for i in reversed(range(self.right_layout.count())): 
            self.right_layout.itemAt(i).widget().setParent(None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())