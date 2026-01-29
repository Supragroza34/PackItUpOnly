# Testing Guide

This document provides instructions for running tests and achieving 90% code coverage.

## Backend Testing (Django)

### Prerequisites
Make sure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Running Tests

#### Run all tests:
```bash
python manage.py test KCLTicketingSystems.tests
```

#### Run with coverage:
```bash
coverage run --source='KCLTicketingSystems' manage.py test KCLTicketingSystems.tests
coverage report
coverage html
```

#### View coverage report:
Open `htmlcov/index.html` in your browser after running coverage.

### Test Coverage

The backend tests cover:
- ✅ Ticket model creation and validation
- ✅ Ticket model string representation
- ✅ Ticket model unique constraints
- ✅ API endpoint successful submission
- ✅ All field validation (required fields, format validation)
- ✅ Name/surname validation (no numbers)
- ✅ K-Number validation (no letters)
- ✅ Email format validation
- ✅ Department validation
- ✅ Type of issue validation
- ✅ Duplicate K-Number detection
- ✅ Whitespace stripping
- ✅ Multiple validation errors
- ✅ Edge cases (special characters, long K-Numbers)
- ✅ HTTP method validation

### Expected Coverage: 90%+

## Frontend Testing (React)

### Prerequisites
Make sure you have installed all dependencies:
```bash
cd frontend
npm install
```

### Running Tests

#### Run all tests:
```bash
npm test
```

#### Run tests with coverage:
```bash
npm test -- --coverage --watchAll=false
```

#### Run tests in watch mode:
```bash
npm run test:watch
```

### Test Coverage

The frontend tests cover:
- ✅ Component rendering
- ✅ Form field rendering
- ✅ Input handling and updates
- ✅ K-Number auto-formatting
- ✅ Email auto-generation
- ✅ Department selection
- ✅ Conditional rendering of issue types
- ✅ Issue type options for each department
- ✅ Form validation (client-side)
- ✅ Error message display
- ✅ Form submission
- ✅ Success message display
- ✅ Form reset after submission
- ✅ Server error handling
- ✅ Network error handling
- ✅ Loading states

### Expected Coverage: 90%+

## Running All Tests

### Windows:
```bash
run_tests.bat
cd frontend
npm test -- --coverage --watchAll=false
```

### Linux/Mac:
```bash
chmod +x run_tests.sh
./run_tests.sh
cd frontend
npm test -- --coverage --watchAll=false
```

## Coverage Goals

- **Backend (Django)**: 90%+ coverage
- **Frontend (React)**: 90%+ coverage

## Test Files Structure

```
KCLTicketingSystems/
  tests.py                    # Django backend tests

frontend/src/
  components/
    __tests__/
      TicketForm.test.js      # React component tests
  App.test.js                 # App component tests
  setupTests.js               # Test configuration
```

## Continuous Integration

To integrate into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run Django tests
  run: |
    pip install -r requirements.txt
    coverage run --source='KCLTicketingSystems' manage.py test
    coverage report --fail-under=90

- name: Run React tests
  run: |
    cd frontend
    npm install
    npm test -- --coverage --watchAll=false --ci
```

