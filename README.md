# CheckMeasureAI 🏗️

> AI-Powered Construction Material Calculation Assistant for Australian Residential Projects

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-v18.2+-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-green.svg)](https://fastapi.tiangolo.com/)

CheckMeasureAI revolutionizes construction material calculations by combining intelligent PDF analysis with AI-powered optimization. Designed specifically for Australian structural engineers and builders, it automates material takeoffs and generates professional cutting lists from architectural drawings.

## ✨ Features

### 🎯 **Core Functionality**
- **Intelligent PDF Analysis** - Upload architectural drawings and extract measurements automatically
- **Traditional Calculations** - Manual input with comprehensive material selection logic
- **AI-Enhanced Multi-Agent System** - Advanced optimization and cost analysis
- **Professional Cutting Lists** - Industry-standard format with waste calculations

### 🤖 **AI-Powered Enhancements**
- **Smart Recommendations** - Spacing optimization and cost-saving suggestions
- **Cost Estimation** - Real-time pricing in AUD with material breakdowns
- **Environmental Impact** - Carbon footprint and sustainability ratings
- **Material Efficiency** - Waste reduction and cutting optimization
- **Delivery Planning** - Logistics optimization and scheduling

### 🏗️ **Australian Standards Compliance**
- **AS1684 Integration** - Australian building standards compliance
- **LVL & Treated Pine** - Standard Australian construction materials
- **Reference Coding** - Industry-standard naming (L1-J1, GF-B2, etc.)
- **Load Calculations** - Residential, commercial, and industrial loads

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** - Backend API server
- **Node.js 18+** - Frontend development
- **npm or yarn** - Package management

### 1. Clone the Repository
```bash
git clone https://github.com/Larksa/checkmeasure-ai.git
cd checkmeasure-ai
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python3 main.py
```
Backend will be available at `http://localhost:8000`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```
Frontend will be available at `http://localhost:3000`

### 4. Access the Application
Open your browser to `http://localhost:3000` and start calculating!

## 📖 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed development environment setup
- **[API Documentation](docs/API.md)** - Complete API endpoint reference
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide

## 🏗️ Architecture

CheckMeasureAI uses a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │  Multi-Agent    │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   System        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF.js        │    │   PyMuPDF       │    │   Claude AI     │
│   Viewer        │    │   Processing    │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components
- **Frontend**: React 18 + TypeScript + Ant Design
- **Backend**: FastAPI + Python 3.11 + AsyncIO
- **PDF Processing**: PyMuPDF + OpenCV + Tesseract OCR
- **AI Integration**: Claude AI for enhanced analysis
- **Multi-Agent System**: Distributed calculation engine

## 🧮 Example Calculation

Input a 4.2m span with 450mm joist spacing:

```json
{
  "span_length": 4.2,
  "joist_spacing": 0.45,
  "building_level": "L1",
  "room_type": "living",
  "load_type": "residential"
}
```

Output includes:
- **10 joists** required (200x45 E13 LVL)
- **8.4m blocking** length
- **Professional cutting list** with waste calculations
- **AI recommendations** for optimization
- **Cost estimation** in AUD
- **Environmental impact** assessment

## 🛠️ Development

### Project Structure
```
checkmeasure-ai/
├── frontend/          # React TypeScript application
├── backend/           # FastAPI Python server
├── docs/             # Documentation
├── scripts/          # Development scripts
└── examples/         # Sample files
```

### Key Technologies
- **Frontend**: React, TypeScript, Ant Design, PDF.js, Konva
- **Backend**: FastAPI, PyMuPDF, OpenCV, Asyncio
- **AI**: Claude AI, Multi-agent architecture
- **Standards**: AS1684 Australian building codes

### Development Scripts
```bash
# Start both frontend and backend
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📋 Roadmap

### Current Version (v1.0)
- ✅ Core joist calculations
- ✅ PDF upload and basic analysis
- ✅ Multi-agent system
- ✅ Professional cutting lists

### Upcoming Features (v1.1)
- 🔄 Wall framing calculations
- 🔄 Rafter and roof calculations
- 🔄 Advanced PDF dimension extraction
- 🔄 Multi-story load transfer
- 🔄 Enhanced mobile support

### Future Enhancements (v2.0)
- 🔮 3D visualization
- 🔮 BIM integration
- 🔮 Cost database integration
- 🔮 Supplier API connections

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Australian building standards (AS1684)
- FastAPI and React communities
- PDF.js and PyMuPDF libraries
- Claude AI for intelligent analysis

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Larksa/checkmeasure-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Larksa/checkmeasure-ai/discussions)
- **Documentation**: [Wiki](https://github.com/Larksa/checkmeasure-ai/wiki)

---

<div align="center">
Made with ❤️ for the Australian construction industry
</div>