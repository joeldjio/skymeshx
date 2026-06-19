# ROS2 Bag Compression Benchmark

Tool for comparing compression algorithms for ROS2 bag recording.

## Overview

The bag compression benchmark tool compares different compression algorithms (zstd, lz4, none) in terms of:
- **File size** (compression ratio)
- **CPU usage** during recording
- **Memory usage** during recording
- **Recording overhead** (time per message)

This helps you choose the optimal compression for your use case.

## Why Compression Matters

### Without Compression
- **File size**: ~100-500 MB per 10-minute flight
- **Disk I/O**: High write load
- **Storage**: Fills up SD cards quickly (especially on Raspberry Pi)

### With Compression
- **File size**: ~20-100 MB (2-5x smaller)
- **Disk I/O**: Reduced write load
- **Storage**: More flights per SD card
- **Trade-off**: Slightly higher CPU usage

## Usage

### Basic Benchmark

```bash
# Run 30-second benchmark on default topics
python tools/benchmark_bag_compression.py

# Custom duration
python tools/benchmark_bag_compression.py --duration 60

# Custom topics
python tools/benchmark_bag_compression.py \
    --topics /fmu/out/vehicle_odometry /fmu/out/vehicle_attitude /fmu/out/vehicle_gps_position
```

### Advanced Options

```bash
# Test specific compressions only
python tools/benchmark_bag_compression.py --compressions zstd lz4

# Keep bag files after benchmark
python tools/benchmark_bag_compression.py --keep-bags

# Save results to JSON
python tools/benchmark_bag_compression.py --save-json

# Custom output directory
python tools/benchmark_bag_compression.py --output-dir ./my_benchmarks
```

### Full Example

```bash
# Comprehensive benchmark: 2 minutes, all topics, save results
python tools/benchmark_bag_compression.py \
    --duration 120 \
    --topics /fmu/out/vehicle_odometry /fmu/out/vehicle_attitude /fmu/out/vehicle_gps_position \
    --compressions none lz4 zstd \
    --save-json \
    --output-dir ./benchmark_results
```

## Output

### Console Output

```
======================================================================
ROS2 Bag Compression Benchmark
======================================================================
Topics: /fmu/out/vehicle_odometry, /fmu/out/vehicle_attitude
Duration: 30s
Compressions: none, lz4, zstd
======================================================================

[NONE] Starting benchmark...

  File Size:     45.23 MB
  Messages:      1500
  Duration:      30.1s
  CPU (avg/max): 8.5% / 12.3%
  RAM (avg/max): 42.1 MB / 55.2 MB
  Overhead:      0.020 ms/msg

[LZ4] Starting benchmark...

  File Size:     28.45 MB
  Messages:      1500
  Duration:      30.1s
  CPU (avg/max): 12.3% / 18.5%
  RAM (avg/max): 48.3 MB / 62.1 MB
  Overhead:      0.020 ms/msg

[ZSTD] Starting benchmark...

  File Size:     18.92 MB
  Messages:      1500
  Duration:      30.1s
  CPU (avg/max): 18.7% / 25.4%
  RAM (avg/max): 55.8 MB / 72.3 MB
  Overhead:      0.020 ms/msg

======================================================================
BENCHMARK SUMMARY
======================================================================

Compression  Size (MB)    Ratio    CPU %      RAM (MB)     Speed     
----------------------------------------------------------------------
none         45.23        -        8.5        42.1         0.020     
lz4          28.45        1.59x    12.3       48.3         0.020     
zstd         18.92        2.39x    18.7       55.8         0.020     
----------------------------------------------------------------------

RECOMMENDATIONS:
----------------------------------------------------------------------
✓ Best Compression:  ZSTD (2.39x smaller)
✓ Lowest CPU Usage:  NONE (8.5% avg)
✓ Best Balance:      LZ4 (size: 28.5MB, cpu: 12.3%)
```

### JSON Output

When using `--save-json`, results are saved to `benchmark_results.json`:

```json
{
  "timestamp": "2026-06-09T15:30:00.000000",
  "results": [
    {
      "compression": "none",
      "file_size_mb": 45.23,
      "duration_sec": 30.1,
      "message_count": 1500,
      "cpu_percent_avg": 8.5,
      "cpu_percent_max": 12.3,
      "memory_mb_avg": 42.1,
      "memory_mb_max": 55.2,
      "compression_ratio": 1.0,
      "recording_overhead_ms": 0.020
    },
    {
      "compression": "lz4",
      "file_size_mb": 28.45,
      "duration_sec": 30.1,
      "message_count": 1500,
      "cpu_percent_avg": 12.3,
      "cpu_percent_max": 18.5,
      "memory_mb_avg": 48.3,
      "memory_mb_max": 62.1,
      "compression_ratio": 1.59,
      "recording_overhead_ms": 0.020
    },
    {
      "compression": "zstd",
      "file_size_mb": 18.92,
      "duration_sec": 30.1,
      "message_count": 1500,
      "cpu_percent_avg": 18.7,
      "cpu_percent_max": 25.4,
      "memory_mb_avg": 55.8,
      "memory_mb_max": 72.3,
      "compression_ratio": 2.39,
      "recording_overhead_ms": 0.020
    }
  ]
}
```

## Compression Algorithms

### None (Uncompressed)
- **Pros**: Lowest CPU usage, fastest recording
- **Cons**: Largest file size
- **Use case**: High-frequency data, CPU-constrained systems

### LZ4
- **Pros**: Fast compression, low CPU overhead, good balance
- **Cons**: Moderate compression ratio
- **Use case**: Real-time recording, embedded systems (Raspberry Pi)
- **Compression**: ~1.5-2x smaller than uncompressed

### ZSTD (Zstandard)
- **Pros**: Best compression ratio, modern algorithm
- **Cons**: Higher CPU usage
- **Use case**: Long-duration flights, storage-constrained systems
- **Compression**: ~2-3x smaller than uncompressed

## Recommendations by Use Case

### Raspberry Pi (Limited Storage)
```bash
# Use ZSTD for maximum space savings
compression: "zstd"
```
- **Why**: SD cards have limited space, CPU overhead is acceptable
- **Trade-off**: ~10-15% more CPU usage for 2-3x smaller files

### High-Frequency Data (>100 Hz)
```bash
# Use LZ4 for balance
compression: "lz4"
```
- **Why**: Fast compression keeps up with high data rates
- **Trade-off**: Moderate file size reduction

### Short Flights (<5 minutes)
```bash
# Use none for simplicity
compression: "none"
```
- **Why**: File size is manageable, no CPU overhead
- **Trade-off**: Larger files

### Long Experiments (>30 minutes)
```bash
# Use ZSTD for maximum savings
compression: "zstd"
```
- **Why**: File size becomes critical over time
- **Trade-off**: Higher CPU usage is worth the space savings

## Integration with ROS2BagRecorder

The benchmark results can guide your choice in `ROS2BagRecorder`:

```python
from skymeshx.ros.bag_recorder import ROS2BagRecorder

# Create recorder
recorder = ROS2BagRecorder(output_dir="./bags")

# Start recording with chosen compression
recorder.start_recording(
    topics=["/fmu/out/vehicle_odometry", "/fmu/out/vehicle_attitude"],
    compression="zstd"  # or "lz4" or "none"
)

# ... fly drone ...

# Stop recording
recorder.stop_recording()
```

## Performance Tips

1. **Run benchmark on target hardware** - Results vary by CPU
2. **Use realistic topics** - Different data types compress differently
3. **Test with actual flight data** - Simulated data may compress differently
4. **Monitor disk I/O** - Compression reduces write load
5. **Consider battery life** - Higher CPU usage = more power consumption

## Troubleshooting

### "No module named 'psutil'"
```bash
pip install psutil>=5.9
```

### "ros2: command not found"
Ensure ROS2 is installed and sourced:
```bash
source /opt/ros/humble/setup.bash  # or your ROS2 distro
```

### High CPU usage during benchmark
This is expected - the benchmark measures CPU usage of the recording process.

### Benchmark fails with timeout
Increase duration or reduce number of topics:
```bash
python tools/benchmark_bag_compression.py --duration 10 --topics /fmu/out/vehicle_odometry
```

## See Also

- [ROS2 Bag Documentation](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html)
- [ZSTD Algorithm](https://facebook.github.io/zstd/)
- [LZ4 Algorithm](https://lz4.github.io/lz4/)
- `skymeshx/ros/bag_recorder.py` - ROS2 bag recording implementation