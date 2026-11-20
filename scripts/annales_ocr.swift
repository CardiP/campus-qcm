import Foundation
import PDFKit
import Vision
import AppKit

let input = CommandLine.arguments[1]
let output = CommandLine.arguments[2]
guard let doc = PDFDocument(url: URL(fileURLWithPath: input)) else { fatalError("Cannot open PDF") }
var pages: [[String: Any]] = []
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let bounds = page.bounds(for: .mediaBox)
    let image = page.thumbnail(of: NSSize(width: bounds.width * 2.5, height: bounds.height * 2.5), for: .mediaBox)
    var rect = CGRect(origin: .zero, size: image.size)
    guard let cg = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { fatalError("No image") }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["fr-FR", "en-US"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: cg).perform([request])
    let lines = (request.results ?? []).compactMap { result -> [String: Any]? in
        guard let cand = result.topCandidates(1).first else { return nil }
        let b = result.boundingBox
        return ["text": cand.string, "bbox": [b.minX * bounds.width, (1-b.maxY) * bounds.height, b.maxX * bounds.width, (1-b.minY) * bounds.height], "confidence": cand.confidence]
    }
    pages.append(["page": i+1, "width": bounds.width, "height": bounds.height, "lines": lines])
    fputs("Page \(i+1): \(lines.count) lines\n", stderr)
}
let data = try JSONSerialization.data(withJSONObject: pages, options: [.prettyPrinted, .sortedKeys])
try data.write(to: URL(fileURLWithPath: output))
