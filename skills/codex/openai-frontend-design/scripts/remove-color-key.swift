#!/usr/bin/env swift

import CoreImage
import Foundation

enum SupportedKey: String {
    case green
    case blue
    case magenta

    var rgb: (red: Float, green: Float, blue: Float) {
        switch self {
        case .green:
            return (0, 1, 0)
        case .blue:
            return (0, 0, 1)
        case .magenta:
            return (1, 0, 1)
        }
    }

    func excess(red: Float, green: Float, blue: Float) -> Float {
        switch self {
        case .green:
            return max(0, green - max(red, blue))
        case .blue:
            return max(0, blue - max(red, green))
        case .magenta:
            return max(0, min(red, blue) - green)
        }
    }
}

enum ColorKeyError: LocalizedError {
    case usage
    case unsupportedKey(String)
    case inputMissing(String)
    case samePath
    case outputExists(String)
    case unreadableImage
    case missingFilter
    case missingOutput
    case missingColorSpace

    var errorDescription: String? {
        switch self {
        case .usage:
            return "Usage: remove-color-key.swift --key green|blue|magenta <input-image> <output.png>"
        case .unsupportedKey(let value):
            return "Unsupported key color: \(value). Expected green, blue, or magenta"
        case .inputMissing(let path):
            return "Input image does not exist: \(path)"
        case .samePath:
            return "Input and output paths must differ; originals are never overwritten"
        case .outputExists(let path):
            return "Output already exists; choose a new path: \(path)"
        case .unreadableImage:
            return "Could not decode the input image"
        case .missingFilter:
            return "Could not create the Core Image color-cube filter"
        case .missingOutput:
            return "The color-cube filter did not return an image"
        case .missingColorSpace:
            return "Could not create the sRGB output color space"
        }
    }
}

func clamp(_ value: Float) -> Float {
    min(max(value, 0), 1)
}

func smoothstep(_ edge0: Float, _ edge1: Float, _ value: Float) -> Float {
    let progress = clamp((value - edge0) / (edge1 - edge0))
    return progress * progress * (3 - 2 * progress)
}

func recoverChannel(observed: Float, key: Float, alpha: Float) -> Float {
    clamp((observed - (1 - alpha) * key) / alpha)
}

func removeColorKey(
    key: SupportedKey,
    inputPath: String,
    outputPath: String
) throws {
    let fileManager = FileManager.default
    let inputURL = URL(fileURLWithPath: inputPath).standardizedFileURL
    let outputURL = URL(fileURLWithPath: outputPath).standardizedFileURL

    guard fileManager.fileExists(atPath: inputURL.path) else {
        throw ColorKeyError.inputMissing(inputURL.path)
    }
    guard inputURL != outputURL else {
        throw ColorKeyError.samePath
    }
    guard !fileManager.fileExists(atPath: outputURL.path) else {
        throw ColorKeyError.outputExists(outputURL.path)
    }
    guard let inputImage = CIImage(
        contentsOf: inputURL,
        options: [.applyOrientationProperty: true]
    ) else {
        throw ColorKeyError.unreadableImage
    }
    guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB) else {
        throw ColorKeyError.missingColorSpace
    }

    let dimension = 64
    let keyRGB = key.rgb
    var cube = [Float]()
    cube.reserveCapacity(dimension * dimension * dimension * 4)

    for blueIndex in 0..<dimension {
        let blue = Float(blueIndex) / Float(dimension - 1)
        for greenIndex in 0..<dimension {
            let green = Float(greenIndex) / Float(dimension - 1)
            for redIndex in 0..<dimension {
                let red = Float(redIndex) / Float(dimension - 1)
                let keyExcess = key.excess(red: red, green: green, blue: blue)
                let alpha = 1 - smoothstep(0.02, 0.92, keyExcess)

                if alpha < 0.015 {
                    cube.append(contentsOf: [0, 0, 0, 0])
                    continue
                }

                // Unmix the known uniform key contribution before
                // premultiplication. This keeps antialiased foreground edges
                // from carrying a green, blue, or magenta fringe.
                let recoveredRed = recoverChannel(
                    observed: red,
                    key: keyRGB.red,
                    alpha: alpha
                )
                let recoveredGreen = recoverChannel(
                    observed: green,
                    key: keyRGB.green,
                    alpha: alpha
                )
                let recoveredBlue = recoverChannel(
                    observed: blue,
                    key: keyRGB.blue,
                    alpha: alpha
                )
                cube.append(contentsOf: [
                    recoveredRed * alpha,
                    recoveredGreen * alpha,
                    recoveredBlue * alpha,
                    alpha,
                ])
            }
        }
    }

    let cubeData = cube.withUnsafeBytes { Data($0) }
    guard let filter = CIFilter(name: "CIColorCubeWithColorSpace") else {
        throw ColorKeyError.missingFilter
    }
    filter.setValue(dimension, forKey: "inputCubeDimension")
    filter.setValue(cubeData, forKey: "inputCubeData")
    filter.setValue(inputImage, forKey: kCIInputImageKey)
    filter.setValue(colorSpace, forKey: "inputColorSpace")

    guard let outputImage = filter.outputImage?.cropped(to: inputImage.extent) else {
        throw ColorKeyError.missingOutput
    }
    let context = CIContext(options: [.cacheIntermediates: false])
    try context.writePNGRepresentation(
        of: outputImage,
        to: outputURL,
        format: .RGBA8,
        colorSpace: colorSpace
    )
}

do {
    guard CommandLine.arguments.count == 5,
          CommandLine.arguments[1] == "--key" else {
        throw ColorKeyError.usage
    }
    let rawKey = CommandLine.arguments[2].lowercased()
    guard let key = SupportedKey(rawValue: rawKey) else {
        throw ColorKeyError.unsupportedKey(rawKey)
    }
    try removeColorKey(
        key: key,
        inputPath: CommandLine.arguments[3],
        outputPath: CommandLine.arguments[4]
    )
    print("key=\(key.rawValue)")
    print("output=\(URL(fileURLWithPath: CommandLine.arguments[4]).standardizedFileURL.path)")
} catch {
    fputs("Error: \(error.localizedDescription)\n", stderr)
    exit(1)
}
