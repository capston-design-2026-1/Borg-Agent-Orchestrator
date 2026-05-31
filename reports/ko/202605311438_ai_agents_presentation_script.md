# AI Agents 발표 대본

- 발표 주제: AI Agent & Agentic Workflow
- 발표 언어: 한국어
- 권장 발표 시간: 15분 00초
- PPTX 발표자 노트에도 동일한 대본이 포함되어 있습니다.
- 제출 전 파일명의 `학번입력필요` 부분을 실제 학번으로 바꾸세요.

## 01. AI Agent는 챗봇이 아니라 실행형 업무 시스템으로 진화하고 있다.

- 권장 시간: 0:40
- 출처/근거: 범위: AI Agent & Agentic Workflow

안녕하세요. 오늘 발표 주제는 최신 AI 및 소프트웨어 기술 트렌드 중 AI Agent와 Agentic Workflow입니다. 핵심 질문은 하나입니다. 왜 우리는 단순한 챗봇이나 코드 자동완성에서 멈추지 않고, 스스로 도구를 호출하고 여러 단계를 수행하는 에이전트를 이야기하게 되었는가입니다. 결론부터 말하면 AI Agent는 사람을 대체하는 마법 상자가 아니라, LLM을 실제 업무 시스템과 연결해 실행 가능한 소프트웨어 런타임으로 만드는 구조입니다.

## 02. 에이전시가 생기는 지점은 모델 능력이 아니라, 도구·상태·통제·관측성이 만나는 지점이다.

- 권장 시간: 0:55
- 출처/근거: OpenAI Agents SDK, Anthropic effective agents

이 발표의 주장은 간단합니다. AI Agent의 본질은 더 똑똑한 모델 하나가 아니라, 모델이 외부 도구를 쓰고, 작업 상태를 기억하고, 필요한 경우 사람에게 승인을 요청하며, 실행 과정을 추적할 수 있는 시스템이라는 점입니다. OpenAI의 Agents SDK 문서도 에이전트를 계획하고 도구를 호출하고 전문 에이전트와 협업하며 멀티스텝 작업을 완료하는 애플리케이션으로 설명합니다. 따라서 기술 분석의 초점은 모델 자체보다 실행 구조에 있습니다.

## 03. LLM은 답을 잘 만들었지만, 기업은 답보다 완료된 업무를 필요로 했다.

- 권장 시간: 1:15
- 출처/근거: Anthropic MCP, McKinsey State of AI 2025

AI Agent가 등장한 배경은 LLM의 한계와 기업 업무의 요구가 만나는 지점에 있습니다. LLM은 문서 요약, 질의응답, 코드 초안처럼 언어 기반 작업에서는 강력했습니다. 하지만 실제 업무는 보통 데이터 조회, 권한 확인, API 호출, 예외 처리, 승인, 기록 남기기까지 이어집니다. 기존 챗봇은 좋은 답변을 주더라도 사용자가 다음 시스템에 들어가 직접 실행해야 했습니다. 그래서 RAG, tool calling, workflow orchestration, MCP 같은 기술이 결합되며 '답변 생성'에서 '업무 완료'로 초점이 이동했습니다.

## 04. 워크플로는 사람이 경로를 설계하고, 에이전트는 상황에 따라 경로를 선택한다.

- 권장 시간: 1:10
- 출처/근거: Anthropic, Building effective agents, 2024

AI Agent를 이해할 때 가장 중요한 구분은 workflow와 agent입니다. Anthropic은 agentic system 안에서도 미리 정해진 코드 경로를 따라가는 workflow와, 모델이 스스로 프로세스와 도구 사용을 선택하는 agent를 구분합니다. 모든 것을 완전 자율 에이전트로 만들 필요는 없습니다. 업무가 반복적이고 규칙이 명확하면 workflow가 더 안전하고 저렴합니다. 반대로 사용자의 목표가 다양하고 중간 판단이 많으며 필요한 도구가 상황마다 달라진다면 agent 방식이 의미를 가집니다.

## 05. 프로덕션 에이전트는 LLM 주변에 실행 계층을 두른 런타임이다.

- 권장 시간: 1:30
- 출처/근거: OpenAI Agents SDK, AWS Bedrock Agents

구조적으로 보면 에이전트는 중앙의 모델 또는 planner만으로 구성되지 않습니다. 사용자의 목표가 들어오면 모델은 계획을 만들고 필요한 도구를 선택합니다. 도구 레지스트리나 MCP 서버는 API, 데이터베이스, 파일 시스템, 업무 애플리케이션을 노출합니다. 메모리와 컨텍스트 계층은 현재 작업 상태와 과거 정보를 관리합니다. 실행기는 도구 호출을 수행하고 결과를 모델에게 되돌립니다. 여기에 guardrail, 권한, 사람 승인, trace와 평가가 붙어야 운영 가능한 시스템이 됩니다.

## 06. 좋은 agentic workflow는 자율성보다 제어 가능한 패턴을 먼저 선택한다.

- 권장 시간: 1:15
- 출처/근거: Anthropic effective agents pattern taxonomy

에이전트를 설계할 때 바로 완전 자율 구조로 가는 것은 위험합니다. Anthropic이 제시한 효과적인 패턴을 보면 prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer처럼 제어 가능한 워크플로부터 시작합니다. 예를 들어 고객 문의를 분류한 뒤 전문 처리기로 보내는 것은 routing입니다. 여러 후보 답변을 만들고 평가자가 고르는 것은 evaluator-optimizer입니다. 이런 패턴은 예측 가능성이 높고 실패 지점을 찾기 쉽습니다. 자율 agent는 이 패턴들로 해결하기 어려운 열린 문제에 적용하는 편이 좋습니다.

## 07. MCP는 에이전트의 USB-C처럼 보이지만, 실제로는 보안 경계를 새로 여는 표준이다.

- 권장 시간: 1:05
- 출처/근거: Anthropic MCP, OpenAI MCP and Connectors

에이전트가 실제 업무를 하려면 외부 시스템과 연결되어야 합니다. 과거에는 서비스마다 별도 커넥터를 만들었지만, MCP는 AI 애플리케이션과 도구 서버 사이의 표준 연결 방식을 제공합니다. Anthropic은 MCP를 데이터가 있는 시스템과 AI assistant를 연결하는 open standard로 설명합니다. OpenAI 문서도 remote MCP server와 connector를 통해 모델이 새 기능에 접근할 수 있다고 설명합니다. 다만 연결이 쉬워진 만큼 민감 데이터 노출, 악성 서버, prompt injection 위험도 커지므로 승인과 allowlist, 로그가 필요합니다.

## 08. 산업 활용은 '대화'보다 '업무 단위 위임'에서 먼저 확산되고 있다.

- 권장 시간: 1:30
- 출처/근거: GitHub Docs, Salesforce, Microsoft Learn, AWS Docs

실제 산업 활용은 네 영역에서 뚜렷합니다. 첫째, 소프트웨어 개발입니다. GitHub Copilot cloud agent는 저장소를 조사하고 계획을 만들고 버그 수정이나 문서 업데이트를 수행한 뒤 브랜치와 커밋, PR까지 이어갈 수 있습니다. 둘째, 고객 서비스와 CRM입니다. Salesforce는 Agentforce 사례로 평균 처리 시간 감소와 행정 채팅 자동 해결, 구독 유지율 개선을 발표했습니다. 셋째, 기업 운영입니다. Microsoft Copilot Studio는 지식 소스와 action을 연결해 장기 작업을 수행하는 agent를 만들 수 있습니다. 넷째, 클라우드 애플리케이션입니다. AWS Bedrock Agents는 foundation model, 데이터 소스, API, knowledge base를 오케스트레이션합니다.

## 09. 채택은 빠르게 넓어졌지만, 완전 자율 운영은 아직 초기 단계다.

- 권장 시간: 1:05
- 출처/근거: McKinsey 2025, Gartner 2025

시장 데이터를 보면 과대광고와 실제 채택 사이의 차이를 볼 수 있습니다. McKinsey의 2025년 조사에서는 응답자의 23퍼센트가 기업 내 어딘가에서 agentic AI를 scaling하고 있고, 39퍼센트는 실험을 시작했다고 답했습니다. 즉 적어도 실험 단계 이상은 62퍼센트입니다. 반면 Gartner는 2025년 조사에서 어떤 형태의 AI agent를 파일럿 또는 배포 중인 비율은 75퍼센트라고 보도했지만, 완전 자율 agent를 고려, 파일럿, 배포 중인 비율은 15퍼센트라고 했습니다. 핵심은 관심은 높지만 성숙도는 아직 제한적이라는 점입니다.

## 10. RPA는 정해진 버튼을 누르고, copilot은 사용자를 돕고, agent는 다음 행동을 제안하고 실행한다.

- 권장 시간: 1:00
- 출처/근거: 비교 분석

기존 자동화와의 차이를 보면 의미가 더 선명합니다. RPA는 화면이나 API 절차가 고정되어 있을 때 강합니다. Copilot은 사람이 주도하는 작업을 보조합니다. 반면 AI Agent는 목표를 입력받고 중간 단계를 나누며, 필요한 도구를 선택하고, 결과를 확인한 뒤 다음 행동으로 넘어갑니다. 그래서 agent는 단순 자동화보다 유연하지만, 반대로 검증과 권한 관리가 훨씬 중요합니다. 차이는 지능의 유무라기보다 '누가 다음 단계를 결정하는가'에 있습니다.

## 11. 가치는 완전 자동화가 아니라, 반복 업무와 예외 처리를 한 흐름 안에 묶는 데서 나온다.

- 권장 시간: 1:00
- 출처/근거: OpenAI, GitHub, Salesforce 사례 종합

AI Agent의 장점은 크게 네 가지입니다. 첫째, 여러 시스템을 오가던 작업 시간을 줄입니다. 둘째, 사람은 목표와 검토에 집중하고 agent가 검색, 초안, 실행 준비를 담당합니다. 셋째, 로그와 trace를 남기면 어떤 도구를 왜 호출했는지 운영 관점에서 확인할 수 있습니다. 넷째, 개인 assistant를 넘어 조직의 업무 프로세스에 연결될 수 있습니다. 그래서 좋은 agent는 사람을 완전히 빼는 시스템이 아니라, 사람이 더 중요한 판단에 시간을 쓰도록 반복 실행을 흡수하는 시스템입니다.

## 12. 에이전트의 약점은 환각보다 권한 있는 행동이 잘못 실행되는 순간에 커진다.

- 권장 시간: 1:25
- 출처/근거: OWASP LLM Top 10, OpenAI guardrails/MCP safety

에이전트의 리스크는 일반 LLM보다 더 큽니다. 단순 답변 오류는 수정하면 되지만, 도구 호출 오류는 실제 데이터 변경, 비용 발생, 개인정보 노출로 이어질 수 있습니다. OWASP는 prompt injection, insecure output handling, excessive agency, overreliance 같은 위험을 제시합니다. OpenAI의 MCP 문서도 remote server가 데이터 접근과 action 수행 권한을 가질 수 있으므로 신뢰된 서버, 승인, 로깅, 데이터 검토가 필요하다고 설명합니다. 따라서 에이전트 보안의 핵심은 최소 권한, 민감 작업 승인, sandbox, allowlist, trace, 평가입니다.

## 13. 다음 경쟁력은 더 자율적인 agent보다, 운영 가능한 AgentOps 체계를 만드는 데 있다.

- 권장 시간: 0:55
- 출처/근거: 종합 전망

향후 전망은 세 단계로 볼 수 있습니다. 단기적으로는 고객 지원, 개발, 사내 검색, 운영 자동화처럼 범위가 명확한 vertical agent가 늘어날 것입니다. 중기적으로는 MCP 같은 표준과 multi-agent 협업이 확산되며 도구 연결 비용이 낮아질 것입니다. 장기적으로는 agent의 행동을 평가하고 추적하고 비용과 리스크를 관리하는 AgentOps가 중요해집니다. 결국 성공 조건은 모델 성능 하나가 아니라, 업무 재설계, 데이터 품질, 권한 정책, 관측성, human-in-the-loop를 함께 설계하는 능력입니다.

## 14. 결론: Agent는 최신 유행어가 아니라 소프트웨어 실행 구조의 변화다.

- 권장 시간: 0:15
- 출처/근거: 참고문헌 및 Q&A

정리하면 AI Agent는 LLM을 실제 산업 시스템에 연결하려는 흐름에서 등장했습니다. 개념은 간단하지만 운영은 어렵습니다. 성공적인 적용은 완전 자율을 목표로 하기보다, 작은 업무 단위에서 도구 연결, 승인, 평가, 관측성을 갖춘 구조로 시작하는 것입니다. 이상으로 발표를 마치겠습니다. 감사합니다.

## 참고문헌

1. Anthropic, Building effective agents, 2024, https://www.anthropic.com/engineering/building-effective-agents
2. OpenAI Developers, Agents SDK, https://developers.openai.com/api/docs/guides/agents
3. OpenAI Agents SDK Guardrails, https://openai.github.io/openai-agents-js/guides/guardrails/
4. OpenAI Agents SDK Tracing, https://openai.github.io/openai-agents-python/tracing/
5. Anthropic, Introducing the Model Context Protocol, 2024, https://www.anthropic.com/news/model-context-protocol
6. OpenAI Developers, MCP and Connectors, https://developers.openai.com/api/docs/guides/tools-connectors-mcp
7. McKinsey, The State of AI 2025: Agents, Innovation, and Transformation, https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/november%202025/the-state-of-ai-2025-agents-innovation_cmyk-v1.pdf
8. Gartner, AI agents survey press release, 2025, https://www.gartner.com/en/newsroom/press-releases/2025-09-30-gartner-survey-finds-just-15-percent-of-it-application-leaders-are-considering-piloting-or-deploying-fully-autonomous-ai-agents
9. GitHub Docs, Copilot cloud agent, https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent
10. Salesforce Investor News, Agentforce 3, 2025, https://investor.salesforce.com/news/news-details/2025/Salesforce-Launches-Agentforce-3-to-Solve-the-Biggest-Blockers-to-Scaling-AI-Agents-Visibility-and-Control/default.aspx
11. Microsoft Learn, Copilot Studio 2025 release wave 1, https://learn.microsoft.com/en-us/power-platform/release-plan/2025wave1/microsoft-copilot-studio/
12. AWS Docs, Amazon Bedrock Agents, https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
13. OWASP Top 10 for Large Language Model Applications, https://owasp.org/www-project-top-10-for-large-language-model-applications/
