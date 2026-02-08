#!/bin/bash
# Setup PreTeXt cache to work around bug in versions 2.32.0-2.36.0
# where rs_services.xml is not found when the download fails.

set -e

# Get PreTeXt version
PTX_VERSION=$(pretext --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "PreTeXt version: $PTX_VERSION"

# Create cache directory
CACHE_DIR="$HOME/.ptx/$PTX_VERSION/rs_cache"
mkdir -p "$CACHE_DIR"

# Check if rs_services.xml already exists
if [ -f "$CACHE_DIR/rs_services.xml" ]; then
    echo "Cache file rs_services.xml already exists"
    exit 0
fi

# Check if runestone_services.xml exists and copy it
if [ -f "$CACHE_DIR/runestone_services.xml" ]; then
    echo "Copying runestone_services.xml to rs_services.xml"
    cp "$CACHE_DIR/runestone_services.xml" "$CACHE_DIR/rs_services.xml"
    exit 0
fi

# Create a minimal fallback cache file if neither exists
# Note: These are fallback values for RuneStone Services version 7.10.0.
# The hardcoded asset filenames with hashed identifiers may become outdated
# as RuneStone releases new versions, but they provide a working baseline
# when network access is unavailable.
echo "Creating minimal fallback cache file"
cat > "$CACHE_DIR/rs_services.xml" << 'EOF'
<?xml version="1.0" ?>
<all>
	<js type="list">
		<item type="str">prefix-runtime.f91c1a4dc12163f2.bundle.js</item>
		<item type="str">prefix-723.3e6434f80549315a.bundle.js</item>
		<item type="str">prefix-runestone.fe35e59c546f8d19.bundle.js</item>
	</js>
	<css type="list">
		<item type="str">prefix-723.3bccd435914aa0ff.css</item>
		<item type="str">prefix-runestone.557d81b04b3ec0e4.css</item>
	</css>
	<cdn-url type="str">https://runestone.academy/cdn/runestone/</cdn-url>
	<version type="str">7.10.0</version>
</all>
EOF

echo "Cache file created successfully"
