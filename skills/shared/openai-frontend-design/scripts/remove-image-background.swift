#!/usr/bin/env swift

import AppKit
import CoreImage
import Foundation
import Vision

enum MattingError: LocalizedError {
    case usage
    case unsupportedSystem
    case inputMissing(String)
    case samePath
    case outputExists(String)
    case unreadableImage
    case noForeground
    case missingColorSpace
    case invalidTrimRadius

    var errorDescription: String? {
        switch self {
        case .usage:
            return "Usage: remove-image-background.swift <input-image> <output.png> [trim-radius]"
        case .unsupportedSystem:
            return "Foreground instance masking requires macOS 14 or newer"
        case .inputMissing(let path):
            return "Input image does not exist: \(path)"
        case .samePath:
            return "Input and output paths must differ; originals are never overwritten"
        case .outputExists(let path):
            return "Output already exists; choose a new path: \(path)"
        case .unreadableImage:
            return "Could not decode the input image"
        case .noForeground:
            return "Vision did not detect a foreground instance"
        case .missingColorSpace:
            return "Could not create the sRGB output color space"
        case .invalidTrimRadius:
            return "Trim radius must be a number from 0 through 24"
        }
    }
}

func removeBackground(
    inputPath: String,
    outputPath: String,
    trimRadius: Double
) throws {
    guard #available(macOS 14.0, *) else {
        throw MattingError.unsupportedSystem
    }

    let fileManager = FileManager.default
    let inputURL = URL(fileURLWithPath: inputPath).standardizedFileURL
    let outputURL = URL(fileURLWithPath: outputPath).standardizedFileURL

    guard fileManager.fileExists(atPath: inputURL.path) else {
        throw MattingError.inputMissing(inputURL.path)
    }
    guard inputURL != outputURL else {
        throw MattingError.samePath
    }
    guard !fileManager.fileExists(atPath: outputURL.path) else {
        throw MattingError.outputExists(outputURL.path)
    }
    guard let inputImage = CIImage(
        contentsOf: inputURL,
        options: [.applyOrientationProperty: true]
    ) else {
        throw MattingError.unreadableImage
    }

    let handler = VNImageRequestHandler(ciImage: inputImage)
    let request = VNGenerateForegroundInstanceMaskRequest()
    try handler.perform([request])

    guard let observation = request.results?.first,
          !observation.allInstances.isEmpty else {
        throw MattingError.noForeground
    }

    let maskedBuffer = try observation.generateMaskedImage(
        ofInstances: observation.allInstances,
        from: handler,
        croppedToInstancesExtent: false
    )
    let imageExtent = inputImage.extent
    let maskedImage = CIImage(cvPixelBuffer: maskedBuffer).cropped(to: imageExtent)
    let alphaVector = CIVector(x: 0, y: 0, z: 0, w: 1)
    let zeroVector = CIVector(x: 0, y: 0, z: 0, w: 0)
    let alphaMask = maskedImage.applyingFilter(
        "CIColorMatrix",
        parameters: [
            "inputRVector": alphaVector,
            "inputGVector": alphaVector,
            "inputBVector": alphaVector,
            "inputAVector": alphaVector,
            "inputBiasVector": zeroVector,
        ]
    )
    let closedMask = alphaMask
        .applyingFilter(
            "CIMorphologyMaximum",
            parameters: ["inputRadius": 12.0]
        )
        .applyingFilter(
            "CIMorphologyMinimum",
            parameters: ["inputRadius": 12.0]
        )
        .cropped(to: imageExtent)
    let cleanMask = closedMask
        .applyingFilter(
            "CIMorphologyMinimum",
            parameters: ["inputRadius": trimRadius]
        )
        .applyingFilter(
            "CIGaussianBlur",
            parameters: [kCIInputRadiusKey: 0.65]
        )
        .cropped(to: imageExtent)
    let transparentBackground = CIImage(
        color: CIColor(red: 0, green: 0, blue: 0, alpha: 0)
    ).cropped(to: imageExtent)
    let outputImage = inputImage.applyingFilter(
        "CIBlendWithMask",
        parameters: [
            kCIInputBackgroundImageKey: transparentBackground,
            kCIInputMaskImageKey: cleanMask,
        ]
    )
    let context = CIContext(options: [.cacheIntermediates: false])

    guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB) else {
        throw MattingError.missingColorSpace
    }

    try context.writePNGRepresentation(
        of: outputImage,
        to: outputURL,
        format: .RGBA8,
        colorSpace: colorSpace
    )
}

do {
    guard (3...4).contains(CommandLine.arguments.count) else {
        throw MattingError.usage
    }

    let trimRadius = CommandLine.arguments.count == 4
        ? Double(CommandLine.arguments[3])
        : 3.0
    guard let trimRadius, (0...24).contains(trimRadius) else {
        throw MattingError.invalidTrimRadius
    }

    try removeBackground(
        inputPath: CommandLine.arguments[1],
        outputPath: CommandLine.arguments[2],
        trimRadius: trimRadius
    )
    print("output=\(URL(fileURLWithPath: CommandLine.arguments[2]).standardizedFileURL.path)")
} catch {
    fputs("Error: \(error.localizedDescription)\n", stderr)
    exit(1)
}
