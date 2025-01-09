//
//  XUITest.swift
//  XUITest
//
//  Created by Marvin Willms on 21.05.24.
//

import XCTest


enum VerticalScrollDirection {
    case up
    case down
}

enum HorizontalScrollDirection {
    case left
    case right
}

class TapCoordinate {
    let x: Double
    let y: Double

    init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }
}

final class XUITest: XCTestCase {

    let app = XCUIApplication()

//    static let lottieAnimationNavButton = TapCoordinate(x: 0.5, y: 0.44396551724137934)
//    static let lottieAnimationPageTogglePlayButton = TapCoordinate(x: 0.5, y: 0.7481527093596059)
//
//    static let videoScreenNavButton = TapCoordinate(x: 0.5, y: 0.5059523809523809)
//    static let videoScreenTogglePlayButton = TapCoordinate(x: 0.5, y: 0.6656019088669951)
//
//    static let galleryNavButton = TapCoordinate(x: 0.5, y: 0.5679392446633825)
//
//    static let contactAppNavButton = TapCoordinate(x: 0.5, y: 0.6299261083743842)
//    static let contactAppAddContactButton = TapCoordinate(x: 0.9253333333333333, y: 0.08866995073891626) // TODO: All action buttons are the same or similar, make them one like backButton
//    static let contactAppSaveContactButton = TapCoordinate(x: 0.9253333333333333, y: 0.08866995073891626)
//    static let firstNameTextField = TapCoordinate(x: 0.6333333333333333, y: 0.15701970443349753)
//    static let lastNameTextField = TapCoordinate(x: 0.6333333333333333, y: 0.21982758620689655)
//    static let phoneTextField = TapCoordinate(x: 0.6333333333333333, y: 0.28263546798029554)
//    static let emailTextField = TapCoordinate(x: 0.6333333333333333, y: 0.34544334975369456)
//
//    static let toggleRecordingButton = TapCoordinate(x: 0.912, y: 0.08866995073891626)
//
    static let backButton = TapCoordinate(x: 0.088, y: 0.08866995073891626)

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app.activate()
    }

    override func tearDown() {
        app.terminate()
        super.tearDown()
    }

    func waitFor(seconds: Double = 0.25) {
        let expectation = XCTestExpectation(description: "Wait for \(seconds) seconds")

        DispatchQueue.global().asyncAfter(deadline: .now() + seconds) {
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: seconds + 1)
    }

    func tapAtNormalized(_ tapCoordinate: TapCoordinate) {
        tapAtNormalized(x: tapCoordinate.x, y: tapCoordinate.y)
    }

    func tapAtNormalized(x: Double, y: Double) {
        let screenSize = app.windows.element(boundBy: 0).frame.size

        let dx = screenSize.width * x
        let dy = screenSize.height * y

        tapAtCoordiantes(x: dx, y: dy)
    }

    func tapAtCoordiantes(x: Double, y: Double) {
        let normalized = app.windows.element(boundBy: 0).coordinate(withNormalizedOffset: CGVector(dx: 0, dy: 0))

        let coordinate = normalized.withOffset(CGVector(dx: x, dy: y))
        coordinate.tap()
    }

    func navigateBack() {
        tapAtNormalized(Self.backButton)
    }

    func scrollHorizontal(_ direction: HorizontalScrollDirection, height: Double) {
        let screenSize = app.windows.element(boundBy: 0).frame.size

        let leftX = screenSize.width * 0.1
        let leftY = screenSize.height * height
        let rightX = screenSize.width * 0.9
        let rightY = screenSize.height * height

        let leftVector = CGVector(dx: leftX / screenSize.width, dy: leftY / screenSize.height)
        let rightVector = CGVector(dx: rightX / screenSize.width, dy: rightY / screenSize.height)

        let leftCoord = app.coordinate(withNormalizedOffset: leftVector)
        let rightCoord = app.coordinate(withNormalizedOffset: rightVector)

        let startTime = Date()
        
        switch direction {
        case .left:
            rightCoord.press(forDuration: 0.01, thenDragTo: leftCoord)
        case .right:
            leftCoord.press(forDuration: 0.01, thenDragTo: rightCoord)
        }
        
        let elapsedTime = Date().timeIntervalSince(startTime)
        let remainingTime = max(0, 3.0 - elapsedTime)
        
        waitFor(seconds: remainingTime)
    }

    func scrollVertical(_ direction: VerticalScrollDirection) {
        let startTime = Date()
        
        switch direction {
        case .up:
            app.swipeDown()
        case .down:
            app.swipeUp()
        }
        
        let elapsedTime = Date().timeIntervalSince(startTime)
        let remainingTime = max(0, 5.0 - elapsedTime)
        
        waitFor(seconds: remainingTime)
    }

    func scrollVertical(_ direction: VerticalScrollDirection, amount: Int) {
        for _ in 1...amount {
            scrollVertical(direction)
        }
    }
    
    func _withRecording(_ function: @escaping () -> Void) -> () -> Void {
        return {
            self.app.buttons["Start Recording"].tap()
            
            function()
            
            self.waitFor(seconds: 1)
            
            self.app.buttons["Stop Recording"].tap()
            
            let element = self.app.staticTexts["Finished Rendering"]
            let exists = element.waitForExistence(timeout: 60 * 5)
            
            XCTAssertTrue(exists, "The recording never finished rendering")
        }
    }
    
    func _withTesting(_ function: @escaping () -> Void) -> () -> Void {
        return {
            let startTime = Date()
            
            self.app.buttons["Start Test"].tap()
            
            function()
            
            self.waitFor()
            
            self.app.buttons["Stop Test"].tap()
            
            let elapsedTime = Date().timeIntervalSince(startTime)
            
            print(elapsedTime)
        }
    }
    
    func _testLottieAnimation() {
        app.buttons["Lottie Animation"].tap()
        waitFor()
        app.buttons["Toggle Play"].tap()
        waitFor(seconds: 10)
        navigateBack()
    }
    
    func testLottieAnimation() {
        _withTesting(_testLottieAnimation)()
    }
    
    func testLottieAnimationWithRecording() {
        _withRecording(testLottieAnimation)()
    }
    
    func _testVideoScreen() {
        app.buttons["Video Screen"].tap()
        waitFor()
        app.buttons["Toggle Play"].tap()
        waitFor(seconds: 10)
        navigateBack()
    }
    
    func testVideoScreen() {
        _withTesting(_testVideoScreen)()
    }
    
    func testVideoScreenWithRecording() {
        _withRecording(testVideoScreen)()
    }
    
    func _testGallery() {
        app.buttons["Gallery"].tap()
        waitFor()
        scrollVertical(.down, amount: 3)
        waitFor()
        navigateBack()
    }
    
    func testGallery() {
        _withTesting(_testGallery)()
    }
    
    func testGalleryWithRecording() {
        _withRecording(testGallery)()
    }
 
    func _testContactApp() {
        app.buttons["Contact App"].tap()
        waitFor()
        scrollHorizontal(.left, height: 0.4)
        scrollHorizontal(.left, height: 0.4)

        scrollVertical(.down, amount: 3)
        waitFor()
        app.buttons["Add Entry"].tap()
        waitFor()
        app.textFields["Firstname"].tap()
        waitFor()
        typeText("Max")
        app.textFields["Lastname"].tap()
        waitFor()
        typeText("Mustermann")
        app.textFields["Phone"].tap()
        waitFor()
        typeText("01234 567890")
        app.textFields["Email"].tap()
        waitFor()
        typeText("max@mustermann.de")

        app.buttons["Save"].tap()
        waitFor()
        navigateBack()
    }
    
    func testContactApp() {
        _withTesting(_testContactApp)()
    }
    
    func testContactAppWithRecording() {
        _withRecording(testContactApp)()
    }

    func _testFullApp() {
        waitFor()

        _testLottieAnimation()

        waitFor()

        _testVideoScreen()

        waitFor()

        _testGallery()

        waitFor()

        _testContactApp()

        waitFor()
    }

    func testFullApp() {
        _withTesting(_testFullApp)()
    }

    func testFullAppWithRecording() {
        _withRecording(testFullApp)()
    }

    func typeText(_ text: String) {
        app.typeText(text)
    }

    func getElementCoordiantes(_ element: XCUIElement) {
        let screenSize = app.windows.element(boundBy: 0).frame.size

        let originX = element.frame.origin.x
        let originY = element.frame.origin.y

        let centerX = originX + (element.frame.width / 2)
        let centerY = originY + (element.frame.height / 2)

        let percentageX = centerX / screenSize.width
        let percentageY = centerY / screenSize.height

        print("\(element.label): TapCoordinate(x: \(percentageX), y: \(percentageY))")
    }
}
