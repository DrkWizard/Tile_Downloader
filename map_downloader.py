import requests
import os
import time
import cv2 as cv
import numpy as np
import math

cwd = os.getcwd()
main = os.path.join(cwd,"map_tile")

TILE_SIZE = 256
def move_point(lat_start, long_start, bearing, distance):
    R = 6371.0  # Radius of the Earth in kilometers

    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat_start)
    lon1 = math.radians(long_start)
    bearing = math.radians(bearing)

    # Calculate new latitude
    lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) +
                     math.cos(lat1) * math.sin(distance / R) * math.cos(bearing))

    # Calculate new longitude
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(lat1),
                             math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))

    # Convert back from radians to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    return lat2, lon2

def bounding_box(center_lat, center_long, side_length):

    # Calculate the coordinates of each corner
    north_lat, north_long = move_point(center_lat, center_long, 0, side_length / 2)
    east_lat, east_long = move_point(center_lat, center_long, 90, side_length / 2)
    south_lat, south_long = move_point(center_lat, center_long, 180, side_length / 2)
    west_lat, west_long = move_point(center_lat, center_long, 270, side_length / 2)

    return north_lat,west_long,south_lat,east_long


def project(lat,lng):
    siny = math.sin(math.radians(lat))
    siny = min(max(siny, -0.9999), 0.9999)
    x = TILE_SIZE * (0.5 + lng/ 360.0)
    y = TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
    return x,y


def pixel_consideration(x_worldCoordinate,y_worldCoordinate,zoom):
    x_pixelCoordinate = x_worldCoordinate * (2**zoom)
    y_pixelCoordinate = y_worldCoordinate * (2**zoom)
    return int(x_pixelCoordinate),int(y_pixelCoordinate)


def tile_consideration(lat,lng,zoom):
    x_world,y_world = project(lat,lng)
    x_pixel,y_pixel = pixel_consideration(x_world,y_world,zoom)
    x_tile = np.floor(x_pixel/256)
    y_tile = np.floor(y_pixel/256)
    return int(x_tile),int(y_tile)


def number_of_tiles(max_zoom_level,top,left,bottom,right,output_dir):
    total_count = 0
    tiles_already_done = 0
    if(max_zoom_level<=22):
        for zoom in range(0,max_zoom_level+1):
            x_tile1,y_tile1 = tile_consideration(top, left,zoom)
            x_tile2,y_tile2 = tile_consideration(top, right,zoom)
            x_tile3,y_tile3 = tile_consideration(bottom, left,zoom)
            x_tile4,y_tile4 = tile_consideration(bottom, right,zoom)

            xs = min(x_tile1,x_tile3)
            xe = max(x_tile2,x_tile4)
            ys = min(y_tile1,y_tile2)
            ye = max(y_tile3,y_tile4)
            s = (ye-ys+1)*(xe-xs+1)
            total_count= total_count+s

            for x in range(xs, xe + 1):
                for y in range(ys, ye + 1):
                    filename = os.path.join(main,output_dir, str(zoom), str(x), f"{y}.jpeg")
                    if os.path.exists(filename):
                        tiles_already_done = tiles_already_done + 1
            remaining_tiles = total_count - tiles_already_done
        return total_count,remaining_tiles, tiles_already_done
    else:
        print("Zoom Level not in range")

    
    
    
    #url_pattern = 'https://mts1.google.com/vt/lyrs=y@186112443&hl=x-local&src=app&x={x}&y={y}&z={z}&s=Galile'
def downloader(zoom, output_dir, xs, xe, ys, ye):
    url_pattern = "https://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga"
    timeout = 10  # Adjust timeout as needed

    if not os.path.exists(main):
        os.makedirs(main)

    if not os.path.exists(os.path.join(main,output_dir)):
        os.makedirs(os.path.join(main,output_dir))

    if not os.path.exists(os.path.join(main,output_dir, str(zoom))):
        os.makedirs(os.path.join(main,output_dir, str(zoom)))

    for x in range(xs, xe + 1):
        if not os.path.exists(os.path.join(main,output_dir, str(zoom), str(x))):
            os.makedirs(os.path.join(main,output_dir, str(zoom), str(x)))

        for y in range(ys, ye + 1):
            filename = os.path.join(os.path.join(main,output_dir, str(zoom), str(x)), f"{y}.jpeg")

            if not os.path.exists(filename):
                url = url_pattern.format(z=zoom, x=x, y=y)
                try:
                    response = requests.get(url=url, stream=True, timeout=timeout)
                    if response.status_code == 200:
                        image = np.asarray(bytearray(response.content), dtype="uint8")
                        image = cv.imdecode(image, cv.IMREAD_COLOR)
                        cv.imwrite(filename, image)
                        print(f" [+] Zoom : {zoom} | Downloader tile {filename}")
                    else:
                        print(f' [+] Failed to download tile {filename} | Status Code: {response.status_code}')
                        time.sleep(5)  # Wait before retrying
                except Exception as e:
                    print(f' [+] Failed to download tile {filename} | Error: {e}')
                    time.sleep(5)  # Wait before retrying


def download_tiles(max_zoom_level, dir_name, top, left, bottom, right):
    if max_zoom_level <= 22:
        for zoom in range(0, max_zoom_level + 1):
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
                time.sleep(5)  # Wait before retrying
                try:
                    downloader(zoom, dir_name, xs, xe, ys, ye)
                except:
                    print(f' [+] Retry failed for zoom level {zoom}. Skipping...')
                    continue

    