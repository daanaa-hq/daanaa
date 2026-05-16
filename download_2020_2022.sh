#!/bin/bash
cd ~/meritgiving
mkdir -p data/xml/2020 data/xml/2022

# Download 2020 index
wget -O data/index_2020.json "https://www.irs.gov/efile-index/2020.json" 2>/dev/null || echo "2020 index not available, manual download needed"

# Download 2022 index  
wget -O data/index_2022.json "https://www.irs.gov/efile-index/2022.json" 2>/dev/null || echo "2022 index not available, manual download needed"

echo "Index files downloaded. Check data/ folder and run parse scripts."
