# world-bank-rai-toolkit
Enhancements for RAI toolkit for July 2021 contract

- [**Country Road Inventory Data**](https://drive.google.com/drive/folders/118YyrT489jJVwFuYaef5LOSfJeAMk2kg)

This project seeks to bridge information from national road inventory systems with road network geometries from OpenStreetMap. This would allow using the authoritative attributes present in road inventory systems to assign road quality attributes to geo-referenced road network features. This enables accurate calculation of UN SDG 9.1.1

This project is focused on extracting road segments from OpenStreetMap given high level description like:
- `RN-01` between `SALCAJA` and `QUETZALTENANGO` in Guatemala
- `RD-ZAC-03-01` from `ZACAPA` until intersection with `CA-10` in Guatemala


Project assume the following:
- Process is only possible if relevant geometries are present in OSM
- Not all road segments may be extracted
- Exact start/end position may need manual adjustment at later time
