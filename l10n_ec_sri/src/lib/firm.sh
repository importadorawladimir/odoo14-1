#!/bin/bash
folder_no_firm="firmar"
folder_firm="firmado"
path_odoo="/home/yordany/.local/share/Odoo/filestore/xml/"

mkdir -p "$path_odoo$folder_no_firm"
mkdir -p "$path_odoo$folder_firm"

for file in $(ls "$path_odoo$folder_no_firm"); do
   rm "$path_odoo$folder_firm/$file.xml"
   source "$path_odoo$folder_no_firm/$file" > "$path_odoo$folder_firm/$file.xml"
   rm "$path_odoo$folder_no_firm/$file"
done

chmod 777 -R "$path_odoo$folder_no_firm"
chmod 777 -R "$path_odoo$folder_firm"

#> "$path_odoo$folder_firm/$file.xml"