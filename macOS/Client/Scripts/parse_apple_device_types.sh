#!/bin/sh

#  parse_apple_device_types.sh
#  Client
#
#  Created by Marvin Willms on 27.01.25.
#

# The file content is from: https://gist.github.com/adamawolf/3048717
INPUT_FILE="apple_device_types.txt"

OUTPUT_FILE="../Client/DeviceModels.swift"

echo "// Auto-generated Swift file for device models" > "$OUTPUT_FILE"
echo "import Foundation" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "let deviceModels: [String: String] = [" >> "$OUTPUT_FILE"

while IFS=":" read -r key value; do
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)

    # Skip empty lines
    if [[ -n "$key" && -n "$value" ]]; then
        echo "    \"$key\": \"$value\"," >> "$OUTPUT_FILE"
    fi
done < "$INPUT_FILE"

echo "]" >> "$OUTPUT_FILE"

echo "Swift dictionary saved to $OUTPUT_FILE"
