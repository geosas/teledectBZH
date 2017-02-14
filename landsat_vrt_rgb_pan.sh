#!/bin/bash

# Convert Landsat 8 GeoTIFF images into RGB pan-sharpened GeoTIFF.
#
# Requirements:
#              * gdal http://www.mapbox.com/tilemill/docs/guides/gdal/
#              * convert (image-magick)
#              * make it able to be executed : chmod +x landsat_vrt_rgb_pan.sh
#
# Reference info: https://gist.github.com/klokan/8832708
#                 http://www.mapbox.com/blog/processing-landsat-8/
#                 http://www.gdal.org/gdal_translate.html
#                 http://www.gdal.org/gdalbuildvrt.html


scene_id="$1"
scene_date="$2"
input_dir="$3"
outpu_dir="$4"

# Change working directory
cd $input_dir

if [[ -z "$scene_id" ]]; then
	echo "Landsat image processing"
	echo ""
	echo "Converts to 8-bit, merges RGB, pan-sharpens and colour corrects"
	echo "Example: ./landsat_vrt_rgb_pan.sh LC82010242013198LGN00 scene_date /input_dir /outpu_dir"
	echo ""
	exit 0
fi

if [ ! -f ./"$scene_id"_B2.TIF ]; then
	echo "File "$scene_id"_B2.TIF not found!"
	exit 0
fi

if [ ! -d "$DIRECTORY" ]; then
	mkdir tmp
fi	

echo "Building virtual RGB composite..."
# Build virtual RGB composite
gdalbuildvrt -overwrite -separate ./tmp/output.vrt "$scene_id"_B4.TIF "$scene_id"_B3.TIF "$scene_id"_B2.TIF 

echo "Creating the RGB composite..."
# Create the RGB composite
gdal_translate -co COMPRESS=DEFLATE -a_nodata 0 ./tmp/output.vrt ./tmp/RGB.TIF

echo "Pan-sharpening RGB image..."
# Pan-sharpen RGB image
gdal_landsat_pansharp -rgb ./tmp/RGB.TIF \
-lum ./tmp/RGB.TIF 0.25 0.22 0.52 -pan "$scene_id"_B8.TIF -ndv 0 -o ./tmp/my_pan.tif

echo "Compressing the pansharpned image..."
# Compress the pansharpned layer
gdal_translate -co COMPRESS=DEFLATE -co photometric=rgb -a_nodata 0 -ot UInt32 -co NBITS=24 -scale ./tmp/my_pan.tif "$outpu_dir"/RGB_"$scene_date".TIF
#gdal_translate -co COMPRESS=DEFLATE -co photometric=rgb -a_nodata 0 ./tmp/my_pan.tif "$outpu_dir"/RGB_"$scene_date".TIF

echo "Création des overviews..."
# Création des overviews
gdaladdo --config COMPRESS_OVERVIEW DEFLATE --config PHOTOMETRIC_OVERVIEW RGB "$outpu_dir"/RGB_"$scene_date".TIF 2 4 8 16

# Remove tmp file
rm -R ./tmp

echo "Finished."
exit
