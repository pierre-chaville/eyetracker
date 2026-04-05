using System;
using System.Collections.Generic;
using System.Threading;
using GazeSpeaker.StreamEngine;
using Fleck;
using System.Text.Json;
using System.Runtime.InteropServices;

namespace HelloApp
{
    class Program
    {
        private static float lastGazeX = 0;
        private static float lastGazeY = 0;
        private static bool hasValidGaze = false;
        private static readonly object gazeLock = new object();
        private static List<IWebSocketConnection> allSockets = new List<IWebSocketConnection>();

        [DllImport("user32.dll")]
        private static extern int GetSystemMetrics(int nIndex);

        [DllImport("user32.dll")]
        private static extern bool EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);

        private const int SM_CXSCREEN = 0;
        private const int SM_CYSCREEN = 1;
        private const int ENUM_CURRENT_SETTINGS = -1;

        [StructLayout(LayoutKind.Sequential)]
        public struct DEVMODE
        {
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string dmDeviceName;
            public short dmSpecVersion;
            public short dmDriverVersion;
            public short dmSize;
            public short dmDriverExtra;
            public int dmFields;
            public int dmPositionX;
            public int dmPositionY;
            public int dmDisplayOrientation;
            public int dmDisplayFixedOutput;
            public short dmColor;
            public short dmDuplex;
            public short dmYResolution;
            public short dmTTOption;
            public short dmCollate;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string dmFormName;
            public short dmLogPixels;
            public int dmBitsPerPel;
            public int dmPelsWidth;
            public int dmPelsHeight;
            public int dmDisplayFlags;
            public int dmDisplayFrequency;
            public int dmICMMethod;
            public int dmICMIntent;
            public int dmMediaType;
            public int dmDitherType;
            public int dmReserved1;
            public int dmReserved2;
            public int dmPanningWidth;
            public int dmPanningHeight;
        }

        static void Main(string[] args)
        {
            Console.WriteLine("GazeSpeaker WebSocket Bridge - Starting...");
            Console.WriteLine($"Process is 64-bit: {Environment.Is64BitProcess}");
            Console.WriteLine($"Operating System is 64-bit: {Environment.Is64BitOperatingSystem}");
            Console.WriteLine("Press Ctrl+C to exit\n");

            // Start WebSocket server
            var server = new WebSocketServer("ws://127.0.0.1:8765");
            server.Start(socket =>
            {
                socket.OnOpen = () =>
                {
                    Console.WriteLine($"WebSocket client connected: {socket.ConnectionInfo.ClientIpAddress}");
                    lock (allSockets)
                    {
                        allSockets.Add(socket);
                    }
                };

                socket.OnClose = () =>
                {
                    Console.WriteLine($"WebSocket client disconnected: {socket.ConnectionInfo.ClientIpAddress}");
                    lock (allSockets)
                    {
                        allSockets.Remove(socket);
                    }
                };

                socket.OnMessage = message =>
                {
                    Console.WriteLine($"Received message: {message}");
                };
            });

            Console.WriteLine("WebSocket server started on ws://127.0.0.1:8765\n");

            try
            {
                // Create API context
                IntPtr apiContext;
                var result = Interop.tobii_api_create(out apiContext, IntPtr.Zero, IntPtr.Zero);
                if (result != tobii_error_t.TOBII_ERROR_NO_ERROR)
                {
                    Console.WriteLine($"Error: Failed to create API context: {result}");
                    return;
                }

                // Enumerate devices
                List<string> urls;
                result = Interop.tobii_enumerate_local_device_urls(apiContext, out urls);
                if (result != tobii_error_t.TOBII_ERROR_NO_ERROR || urls.Count == 0)
                {
                    Console.WriteLine("Error: No eye tracker device found");
                    Interop.tobii_api_destroy(apiContext);
                    return;
                }

                Console.WriteLine($"Found device: {urls[0]}\n");

                // Connect to device
                IntPtr deviceContext;
                result = Interop.tobii_device_create(apiContext, urls[0],
                    Interop.tobii_field_of_use_t.TOBII_FIELD_OF_USE_INTERACTIVE, out deviceContext);
                if (result != tobii_error_t.TOBII_ERROR_NO_ERROR)
                {
                    Console.WriteLine($"Error: Failed to connect to device: {result}");
                    Interop.tobii_api_destroy(apiContext);
                    return;
                }

                // Subscribe to gaze data
                result = Interop.tobii_gaze_point_subscribe(deviceContext, OnGazePoint);
                if (result != tobii_error_t.TOBII_ERROR_NO_ERROR)
                {
                    Console.WriteLine($"Error: Failed to subscribe to gaze data: {result}");
                    Interop.tobii_device_destroy(deviceContext);
                    Interop.tobii_api_destroy(apiContext);
                    return;
                }

                Console.WriteLine("Eye tracking active. Broadcasting gaze data via WebSocket...\n");

                // Get actual screen resolution (not DPI-scaled)
                DEVMODE devMode = new DEVMODE();
                devMode.dmSize = (short)Marshal.SizeOf(devMode);
                int screenWidth = 1920;
                int screenHeight = 1080;

                if (EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref devMode))
                {
                    screenWidth = devMode.dmPelsWidth;
                    screenHeight = devMode.dmPelsHeight;
                    Console.WriteLine($"Actual screen resolution: {screenWidth}x{screenHeight}");
                }
                else
                {
                    // Fallback to scaled dimensions
                    screenWidth = GetSystemMetrics(SM_CXSCREEN);
                    screenHeight = GetSystemMetrics(SM_CYSCREEN);
                    Console.WriteLine($"Screen dimensions (DPI-scaled): {screenWidth}x{screenHeight}");
                }
                Console.WriteLine();

                // Start background thread for processing callbacks
                bool running = true;
                Thread callbackThread = new Thread(() =>
                {
                    while (running)
                    {
                        try
                        {
                            Interop.tobii_device_process_callbacks(deviceContext);
                            Thread.Sleep(10); // Small delay to avoid excessive CPU usage
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Callback error: {ex.Message}");
                            Thread.Sleep(100);
                        }
                    }
                });
                callbackThread.Start();

                // Broadcast coordinates to WebSocket clients
                Console.CancelKeyPress += (sender, e) =>
                {
                    e.Cancel = true;
                    running = false;
                };

                while (running)
                {
                    Thread.Sleep(33); // ~30 FPS

                    lock (gazeLock)
                    {
                        if (hasValidGaze && allSockets.Count > 0)
                        {
                            int pixelX = (int)(lastGazeX * screenWidth);
                            int pixelY = (int)(lastGazeY * screenHeight);

                            var data = new
                            {
                                timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
                                x = lastGazeX,
                                y = lastGazeY,
                                pixelX = pixelX,
                                pixelY = pixelY,
                                screenWidth = screenWidth,
                                screenHeight = screenHeight,
                                valid = true
                            };

                            // Console.WriteLine($"Gaze: ({lastGazeX:F3}, {lastGazeY:F3}) => Pixel: ({pixelX}, {pixelY})");

                            string json = JsonSerializer.Serialize(data);

                            lock (allSockets)
                            {
                                foreach (var socket in allSockets.ToArray())
                                {
                                    try
                                    {
                                        socket.Send(json);
                                    }
                                    catch (Exception ex)
                                    {
                                        Console.WriteLine($"Error sending to client: {ex.Message}");
                                    }
                                }
                            }
                        }
                    }
                }

                // Cleanup
                Console.WriteLine("\nShutting down...");
                callbackThread.Join();
                Interop.tobii_gaze_point_unsubscribe(deviceContext);
                Interop.tobii_device_destroy(deviceContext);
                Interop.tobii_api_destroy(apiContext);
                Console.WriteLine("Cleanup complete.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }

        private static void OnGazePoint(ref tobii_gaze_point_t gazePoint, IntPtr userData)
        {
            lock (gazeLock)
            {
                if (gazePoint.validity == tobii_validity_t.TOBII_VALIDITY_VALID)
                {
                    lastGazeX = gazePoint.position.x;
                    lastGazeY = gazePoint.position.y;
                    hasValidGaze = true;
                }
                else
                {
                    hasValidGaze = false;
                }
            }
        }
    }
}

