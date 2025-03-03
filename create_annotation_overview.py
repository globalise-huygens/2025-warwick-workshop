import json
import requests

import xml.etree.ElementTree as ET


def parse_annotation_target(annotation):

    # xywh is easiest
    if type(annotation["target"]) is str:
        x, y, w, h = annotation["target"].rsplit("=", 1)[1].split(",")

    # svg is harder
    else:
        svg = annotation["target"]["selector"]["value"]
        x, y, w, h = get_bounding_box(svg)

    return x, y, w, h


def get_bounding_box(svg):
    root = ET.fromstring(svg)

    if root.tag == "svg":
        element = next(iter(root), None)
    else:
        element = root

    if element is None:
        return None

    if element.tag == "ellipse":
        cx = int(element.get("cx", 0))
        cy = int(element.get("cy", 0))
        rx = int(element.get("rx", 0))
        ry = int(element.get("ry", 0))
        return (cx - rx, cy - ry, rx * 2, ry * 2)

    elif element.tag == "polygon":
        points = element.get("points", "").strip()
        coords = [tuple(map(int, point.split(","))) for point in points.split()]
        xs, ys = zip(*coords)
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def main(file_path: str):

    with open(file_path, "r") as f:
        manifest = json.load(f)

    md = "# Annotation Output\n\n"

    for canvas in manifest["items"]:
        for annotation_page in canvas.get("annotations", []):
            annotation_page_id = annotation_page["id"]

            annotation_page = requests.get(annotation_page_id).json()

            for annotation in annotation_page["items"]:

                if not annotation["motivation"] == "commenting":
                    continue
                x, y, w, h = parse_annotation_target(annotation)

                image_url = (
                    canvas["items"][0]["items"][0]["body"]["service"][0]["@id"]
                    + f"/{x},{y},{w},{h}/full/0/default.jpg"
                )

                comments = []
                for body in annotation["body"]:
                    if body["type"] == "TextualBody":
                        comments.append(body["value"])

                md += f"![]({image_url})"
                for comment in comments:
                    md += comment + "\n"
                md += "\n\n"

    with open("output.md", "w") as f:
        f.write(md)


if __name__ == "__main__":
    MANIFEST_FILEPATH = "manifest.json"
    main(file_path=MANIFEST_FILEPATH)
