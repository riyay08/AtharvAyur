# Architecture

AtharvAyur is split in two halves — a FastAPI backend structured around
Clean Architecture, and a React (Vite) frontend structured around MVVM.
Both halves apply the same core principle: **business logic lives in
framework-free modules that consume abstract ports, and outer layers wire
those ports to concrete implementations**.

```
atharvayur/
├── backend/         # Clean Architecture: domain → application → infrastructure / interfaces
└── src/             # MVVM: models → services → viewmodels → views (containers compose them)
```

---

## Backend — Clean Architecture

**Dependency rule:** arrows point inward only. Domain depends on nothing.
Application depends on domain and on port _interfaces_ it defines itself.
Infrastructure and interfaces depend on application + domain. Nothing
inward ever imports from an outer layer.

```
app/
├── domain/
│   ├── entities/          # User, HealthProfile, WeeklyPlan, DailyCheckIn, ChatMessage, DailyEnvironmentTip
│   ├── value_objects.py   # Dosha, Pillar, ChatRole, Citation, DateRange, HumidityBand, …
│   ├── services/          # Pure domain logic: SafetyPolicy, PlanNormalization, WeekCalendar,
│   │                      # WeatherInterpretation, ProfileMerge
│   └── errors.py          # Domain-typed exceptions raised by services/use cases
│
├── application/
│   ├── ports/             # Protocols the application layer depends on:
│   │                      #   repositories, LLMGateway, WeatherGateway, TokenService,
│   │                      #   Clock, UnitOfWork
│   ├── dtos.py            # Input/Output dataclasses for use cases (no Pydantic)
│   └── use_cases/         # One class per workflow: IssueAccessToken, UpsertProfile,
│                          # GenerateHealthReply, UpsertCheckIn, GetCheckInWeek,
│                          # GenerateWeeklyPlan, GetCurrentWeeklyPlan,
│                          # GenerateWeeklyPlansForAllUsers, GenerateEnvironmentTip, …
│
├── infrastructure/        # Concrete adapters for ports
│   ├── db/                # SQLAlchemy repositories + UnitOfWork + session factory
│   ├── llm/               # GeminiLLMGateway
│   ├── weather/           # OpenWeatherWeatherGateway
│   ├── auth/              # JoseTokenService
│   └── time/              # SystemClock
│
├── interfaces/http/       # FastAPI-only code
│   ├── routers/           # Thin HTTP adapters that parse requests, invoke use cases, return DTOs
│   ├── schemas/           # Pydantic request/response models (API contract)
│   ├── deps.py            # Dependency Injection: constructs use cases from concrete adapters
│   └── exception_handlers.py
│
├── main.py                # Composition root for the ASGI app (middleware, routers, lifespan)
└── scheduler.py           # Composition root for APScheduler jobs (batch weekly-plan generation)
```

### Rules the backend follows

- **Domain is pure.** No FastAPI, no SQLAlchemy, no network I/O. Entities
  are dataclasses; services are stateless functions/classes.
- **Use cases depend on ports, not vendors.** They take repositories and
  gateways via constructor injection and never import from `infrastructure/`.
- **Infrastructure is replaceable.** Each port has exactly one concrete
  adapter today, but tests substitute in-memory fakes (see
  `backend/tests/fakes.py`) without touching use-case code.
- **HTTP is thin.** Routers only translate between Pydantic schemas and
  use-case DTOs. No business logic lives in routers.
- **Errors flow outward.** Domain errors are caught by
  `interfaces/http/exception_handlers.py` and translated to HTTP responses.

### Testing

- `backend/pytest.ini` configures discovery under `backend/tests/`.
- `backend/tests/fakes.py` provides in-memory implementations of every
  port (repositories, gateways, clock, token service, UoW).
- `backend/tests/domain/` tests pure domain services and entities.
- `backend/tests/application/` tests use cases in isolation by injecting
  fakes.

Run:

```bash
cd backend
./.venv/bin/pytest
```

### Adding a backend feature

1. **Domain.** If you need a new concept, add an entity/value object and
   any pure rules to `domain/services/`. Add a domain error if the rule
   has a named failure.
2. **Ports.** Decide what the use case needs (repository, gateway, etc.).
   Add or extend a Protocol under `application/ports/`.
3. **DTOs & use case.** Add an Input/Output dataclass in
   `application/dtos.py` and a class in `application/use_cases/` that
   orchestrates domain services via injected ports.
4. **Infrastructure.** Implement the port(s) concretely (e.g. a new
   SQLAlchemy repository method).
5. **HTTP.** Add a Pydantic schema in `interfaces/http/schemas/`, wire a
   dependency in `interfaces/http/deps.py`, and add a thin router in
   `interfaces/http/routers/`.
6. **Tests.** Start with the domain rule, then the use case with fakes,
   then — only if justified — an HTTP test.

---

## Frontend — MVVM

**Dependency rule:** views depend on props only. ViewModels depend on
models + services. Containers compose a ViewModel with a View. Nothing
reaches _across_ features (e.g. the chat ViewModel does not import the
plan service).

```
src/
├── models/         # Pure JS: scoring, plan shape, check-in enums, citation trust classification
├── services/       # I/O boundary:
│                   #   apiClient.js        — fetch wrapper (JSON, auth, error mapping)
│                   #   sessionService.js   — JWT token lifecycle
│                   #   storage.js          — localStorage access
│                   #   profileService.js, chatService.js, checkinService.js,
│                   #   planService.js, environmentService.js, geolocationService.js
│
├── viewmodels/     # React hooks that own component state and orchestrate services/models
│                   #   useAppShellViewModel, useQuizViewModel,
│                   #   useDailyCheckInViewModel, useWeeklyPlanViewModel,
│                   #   useDynamicCategoryStackViewModel, useHealthChatViewModel,
│                   #   useDailyTipViewModel, useGeolocation
│
├── views/          # Pure presentational components. Props in, JSX out.
│                   #   QuizView, QuizResultsView, DailyCheckInView,
│                   #   WeeklyPlanView, DynamicCategoryStackView,
│                   #   HealthChatView, DailyEnvironmentTipView
│
├── containers/     # Thin composition: instantiate a ViewModel, pass its state+actions to a View
│                   #   QuizContainer, ChatShellContainer,
│                   #   DailyCheckInContainer, DailyEnvironmentTipContainer,
│                   #   WeeklyPlanContainer, DynamicCategoryStackContainer,
│                   #   HealthChatContainer
│
├── data/           # Static quiz bank + dosha labels
├── App.jsx         # Composition root: `useAppShellViewModel` picks Quiz vs Chat container
└── main.jsx        # React entry
```

### Rules the frontend follows

- **Models are framework-free.** Pure JS, no React, no `fetch`. They are
  the natural home for derivation logic (scoring, date math, enum
  validation, trust classification).
- **Services are the only I/O.** Every `fetch` / `localStorage` /
  `navigator.geolocation` call lives under `services/`. ViewModels
  accept service functions via parameters so tests can inject fakes.
- **ViewModels own state.** They return a plain object of values +
  actions. They do not render.
- **Views are pure.** No state, no `useEffect`, no imports from
  `services/` or `viewmodels/`. They receive everything via props.
- **Containers are thin glue.** A container calls one ViewModel hook and
  hands its output to a View. Cross-feature composition happens in the
  containers layer only (e.g. `ChatShellContainer` wires geolocation to
  the daily-tip and chat containers).

### Testing

- `vite.config.js` configures Vitest with jsdom + Testing Library setup.
- Pure models are tested directly (`src/models/*.test.js`).
- ViewModel hooks are tested with `@testing-library/react`'s
  `renderHook` and fake service functions (`src/viewmodels/*.test.jsx`).

Run:

```bash
npm test
npm run build
```

### Adding a frontend feature

1. **Model.** Extract any derivation / validation into a pure function
   under `models/`. Write tests first.
2. **Service.** If the feature talks to the backend or a browser API,
   add a small module under `services/`. Keep it to one concern.
3. **ViewModel.** Create a `useXxxViewModel` hook that composes the
   service(s) and model(s) into a `{ state, actions }` object. Accept
   the service as a parameter with a default so it can be mocked.
4. **View.** Write a pure component that takes the ViewModel's output
   as props and renders JSX. No hooks other than local UI helpers
   (e.g. refs for DOM scroll).
5. **Container.** Wire (3) and (4) together. Pull only the props the
   View needs from the ViewModel. Cross-feature props (e.g. lat/lon)
   are passed in from a higher container.
6. **Mount.** Reference the container from `App.jsx` or from the
   appropriate shell container.

---

## Why this structure

- **Independent testability.** Domain + application on the backend and
  models + ViewModels on the frontend run entirely in-memory with fakes.
  Zero Postgres, zero network, zero browser API.
- **Swappable I/O.** Replacing Gemini with another LLM, OpenWeather with
  another provider, or swapping the frontend fetch wrapper touches a
  single adapter/service module.
- **Reviewable diffs.** A new feature is a predictable series of small
  files in well-known folders instead of a sprawling patch to a god
  component.
