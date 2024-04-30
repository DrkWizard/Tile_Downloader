import requests
import os
import time
import cv2 as cv
import numpy as np
import math
import threading
from datetime import datetime

cwd = os.getcwd()
main = os.path.join(cwd,"map_tile")
TILE_SIZE = 256


def project(lat,lng,zoom):
    siny = math.sin(math.radians(lat))
    siny = min(max(siny, -0.9999), 0.9999)
    x = TILE_SIZE * (0.5 + lng/ 360.0)
    y = TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    x_pixelCoordinate = x * (2**zoom)
    y_pixelCoordinate = y* (2**zoom)
    return int(x_pixelCoordinate),int(y_pixelCoordinate)


def tile_consideration(lat,lng,zoom):
    x_pixel,y_pixel = project(lat,lng,zoom)
    x_tile = np.floor(x_pixel/256)
    y_tile = np.floor(y_pixel/256)
    return int(x_tile),int(y_tile)


def process_tiles_for_zoom(zoom_range, top, left, bottom, right, output_dir, total_counts, tiles_done):
    for zoom in zoom_range:
        x_tile1, y_tile1 = tile_consideration(top, left, zoom)
        x_tile2, y_tile2 = tile_consideration(top, right, zoom)
        x_tile3, y_tile3 = tile_consideration(bottom, left, zoom)
        x_tile4, y_tile4 = tile_consideration(bottom, right, zoom)

        xs = min(x_tile1, x_tile3)
        xe = max(x_tile2, x_tile4)
        ys = min(y_tile1, y_tile2)
        ye = max(y_tile3, y_tile4)
        s = (ye - ys + 1) * (xe - xs + 1)
        total_counts[zoom] = s
        check_1 =  os.path.join(main,output_dir,str(zoom))
        if(os.path.exists(check_1)):
            for x in range(xs, xe + 1):
                check_2 = os.path.join(check_1,str(x))
                if(os.path.exists(check_2)):
                    for y in range(ys, ye + 1):
                        check_3 = os.path.join(check_2,f"{y}.jpeg")
                        if(os.path.exists(check_3)):
                            tiles_done[zoom] += 1

def number_of_tiles(zoom_start,max_zoom_level, top, left, bottom, right, output_dir):
    total_counts = [0] * (max_zoom_level + 1)
    tiles_done = [0] * (max_zoom_level + 1)

    if max_zoom_level <= 22:
        zoom_range1 = range(zoom_start,max_zoom_level+1,2)
        zoom_range2 = range(zoom_start+1, max_zoom_level + 1,2)

        threads = []
        t1 = threading.Thread(target=process_tiles_for_zoom, args=(zoom_range1, top, left, bottom, right, output_dir, total_counts, tiles_done))
        t2 = threading.Thread(target=process_tiles_for_zoom, args=(zoom_range2, top, left, bottom, right, output_dir, total_counts, tiles_done))

        threads.append(t1)
        threads.append(t2)

        t1.start()
        t2.start()

        for t in threads:
            t.join()

        total_count = sum(total_counts)
        tiles_already_done = sum(tiles_done)
        remaining_tiles = total_count - tiles_already_done
        return total_count, remaining_tiles, tiles_already_done
    else:
        print("Zoom Level not in range")

    
    #url_pattern = 'https://mts1.google.com/vt/lyrs=y@186112443&hl=x-local&src=app&x={x}&y={y}&z={z}&s=Galile'
def downloader(zoom, output_dir, xs, xe, ys, ye):
    url_pattern = "https://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga"
    timeout = 5  # Adjust timeout as needed
    
    if not os.path.exists(os.path.join(main,output_dir, str(zoom))):
        os.makedirs(os.path.join(main,output_dir, str(zoom)))

    for x in range(xs, xe + 1):
        if not os.path.exists(os.path.join(main,output_dir, str(zoom), str(x))):
            os.makedirs(os.path.join(main,output_dir, str(zoom), str(x)))

        for y in range(ys, ye + 1):
            filename = os.path.join(os.path.join(main,output_dir, str(zoom), str(x)), f"{y}.jpeg")

            if not os.path.exists(filename):
                url = url_pattern.format(z=zoom, x=x, y=y)
                response = requests.get(url=url, stream=True, timeout=timeout)
                if response.status_code == 200:
                    image = np.asarray(bytearray(response.content), dtype="uint8")
                    image = cv.imdecode(image, cv.IMREAD_COLOR)
                    cv.imwrite(filename, image)
                    print(f" [+] Zoom : {zoom} | Downloader tile {filename}")
                else:
                    print(f' [+] Failed to download tile {filename} | Status Code: {response.status_code}')


def download_tiles(zoom_start,max_zoom_level, dir_name, top, left, bottom, right):

    if not os.path.exists(os.path.join(main,dir_name)):
        os.makedirs(os.path.join(main,dir_name))
        text_path = os.path.join(main,dir_name,"details.txt")
        with open(text_path, "w") as file:
            file.write(f"""directory: {dir_name}
top: {top}
left: {left}
bottom: {bottom}
right: {right}
zoom start: {zoom_start}
zoom end: {max_zoom_level}
Date downloaded: {datetime.now()}""")
    if max_zoom_level <= 22:
        for zoom in range(zoom_start, max_zoom_level + 1):
            x_tile1, y_tile1 = tile_consideration(top, left, zoom)
            x_tile2, y_tile2 = tile_consideration(top, right, zoom)
            x_tile3, y_tile3 = tile_consideration(bottom, left, zoom)
            x_tile4, y_tile4 = tile_consideration(bottom, right, zoom)
            
            xs = min(x_tile1, x_tile3)
            xe = max(x_tile2, x_tile4)
            ys = min(y_tile1, y_tile2)
            ye = max(y_tile3, y_tile4)
            
            try:
                downloader(zoom, dir_name, xs, xe, ys, ye)
            except Exception as e:
                print(f' [+] Error during download: {e}')
                time.sleep(5)
                try:
                    downloader(zoom, dir_name, xs, xe, ys, ye)
                except:
                    print(f' [+] Failed to download tile | Error: {e}')
                    return False
    return True