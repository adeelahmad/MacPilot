# **MacPilot 🚀: Your AI-Powered macOS Automation Framework**

MacPilot leverages the power of Large Language Models (LLMs) to automate tasks on your Mac. It translates natural language instructions into executable actions, controlling applications and navigating complex workflows hands-free.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

---

## **🌟 Key Features**

- **Natural Language Instruction Processing:**  Give instructions to your Mac in plain English.
- **Dynamic State Management:** Captures the current UI state, including active applications, windows, UI elements, and system information, using native macOS APIs and the Vision framework.  This state is then used by the AI to plan and execute actions.
- **AI-Powered Action Planning:** Uses LLMs to analyze instructions and generate step-by-step action plans based on the current state and available actions.  The plans are structured using Pydantic models for robustness and validation.
- **Actor Stack Framework:** Executes actions on the system.
    - **Generic Actions:**  Control the mouse, keyboard, activate applications, switch windows, and more.
    - **Application-Specific Actors:** Includes pre-built actors for Chrome (browser control) and Finder (file system operations), with the ability to easily extend the framework to support other applications.
- **Pattern Matching (Optional):**  While primarily relying on structured output from the LLM, the framework includes a pattern-matching mechanism for potential optimization of common tasks.
- **State Validation and Recovery:** Validates the UI state after each step and attempts recovery from failures using AI-generated recovery plans.
- **Modular and Extensible:** Designed for easy extension and customization. Add new actors, actions, and patterns to tailor the framework to your specific needs.

---

## **📂 Project Structure**

```
automation_framework/
├── actors/                # Application-specific and generic action implementations
│   ├── base.py
│   ├── chrome/
│   │   └── browser.py
│   ├── finder/
│   │   └── filesystem.py
│   └── generic/
│       └── mouse_keyboard.py
├── core/                  # Core framework components
│   ├── config.py
│   ├── context.py
│   └── metaclasses/
│       └── actor_meta.py
├── examples/              # Example usage scripts
│   └── orchestration_example.py
├── models/                # Data models (Pydantic)
│   ├── base.py
│   ├── db_session.py
│   └── pydantic_models.py
├── services/              # Core services
│   ├── ai/
│   │   └── openai_service.py
│   ├── execution/
│   │   └── engine.py
│   ├── instruction/
│   │   └── processor.py
│   ├── macos_ui_service/
│   │   ├── __init__.py
│   │   └── macos_ui_service.py
│   ├── mapping/
│   │   ├── __init__.py
│   │   └── element_mapper.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── interaction_patterns.py
│   │   ├── pattern_matcher.py
│   │   └── pattern_registry.py
│   ├── state/
│   │   └── manager.py
│   └── validation/
│       ├── __init__.py
│       ├── state_validator.py
│       └── validator.py  # Example validation rules
├── tests/                 # Unit tests
├── utils/                 # Utility functions and decorators
│   └── decorators.py
├── __init__.py
├── __main__.py
└── main.py                # Command-line interface
```

---

## **⚙️ Getting Started**

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/MacPilot.git  # Replace with your repository URL
   cd MacPilot
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run Example Orchestration:**

   ```bash
   python -m automation_framework execute "Open Chrome and go to google.com"  # Example instruction
   ```

---

## **💡 How It Works**

1. **Instruction Input:** Provide a task in natural language.
2. **State Capture:** MacPilot captures the current UI and system state.
3. **AI Planning:**  The LLM analyzes the instruction and state to generate a structured action plan.
4. **Execution:** The Execution Engine executes the plan using the appropriate actors.
5. **Validation and Recovery:** After each step, the state is validated. If a failure occurs, a recovery plan is generated and executed.

---

## **💻 Usage**

See the `examples/` directory for more detailed usage examples, including how to define custom actors and integrate them into the framework.  The `main.py` file provides a command-line interface for executing instructions and listing available capabilities.

---

## **🤝 Contributing**

Contributions are welcome!  Please follow these steps:

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature-name`.
3. Commit your changes: `git commit -m "Add your feature description"`.
4. Push to the branch: `git push origin feature/your-feature-name`.
5. Open a pull request.

---

## **📄 License**

MacPilot is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


