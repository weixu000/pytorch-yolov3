import time

import cv2
import numpy as np
import torch


def load_classes(file_path):
    with open(file_path, "r") as fp:
        names = [x for x in fp.read().split("\n") if x]
    return names


def color_map(n):
    def bit_get(x, i):
        return x & (1 << i)

    cmap = []
    for i in range(n):
        r = g = b = 0
        for j in range(7, -1, -1):
            r |= bit_get(i, 0) << j
            g |= bit_get(i, 1) << j
            b |= bit_get(i, 2) << j
            i >>= 3

        cmap.append((r, g, b))
    return cmap


class DurationTimer:
    def __init__(self):
        self.start, self.end = None, None

    @property
    def duration(self):
        return self.end - self.start

    def __enter__(self):
        self.start, self.end = time.time(), None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        return False


def draw_text(img, label, color, bottom_left=None, upper_right=None):
    t_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1, 1)
    if bottom_left is None:
        assert upper_right is not None
        bottom_left = upper_right[0] - t_size[0], upper_right[1] + t_size[1]
    else:
        assert upper_right is None
        upper_right = bottom_left[0] + t_size[0], bottom_left[1] - t_size[1]

    cv2.rectangle(img, bottom_left, upper_right, color, -1)
    cv2.putText(img, label, bottom_left, cv2.FONT_HERSHEY_PLAIN, 1, [255 - c for c in color])


def cvmat_to_tensor(mat):
    mat = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
    mat = mat.transpose((2, 0, 1))
    mat = torch.from_numpy(mat).float().div(255)
    return mat


def draw_bbox(img, bbox, label_fn=lambda i: '', color_fn=lambda i: [255, 0, 0]):
    """
    Draw bounding boxes on the image
    """
    for i, b in enumerate(bbox):
        b = tuple(b)
        p1, p2 = b[:2], b[2:]
        cv2.rectangle(img, p1, p2, color_fn(i))

        label = label_fn(i)
        if label:
            draw_text(img, label, color_fn(i), bottom_left=p1)


def draw_detections(img, detections, classes, cmap):
    """
    Draw bounding boxes on the image and add class label and confidence score as title
    """
    bbox, cls, scr = detections
    label_fn = lambda i: f'{classes[cls[i].long().item()]} {scr[i].item():.2f}'
    color_fn = lambda i: cmap[cls[i].long().item()]
    draw_bbox(img, bbox.long().numpy(), label_fn, color_fn)


def draw_trackers(img, trackers):
    bbox, id = trackers[:, :-1], trackers[:, -1]
    label_fn = lambda i: f'{int(id[i])}'
    draw_bbox(img, bbox.astype(np.int), label_fn)


def iterate_video(capture):
    while capture.isOpened():
        retval, frame = capture.read()
        if retval:
            yield frame
        else:
            break
