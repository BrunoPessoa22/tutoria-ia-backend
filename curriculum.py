"""
Cultura Builder 18-Month Curriculum
Structured learning path from AI beginner to launching applications
"""

CURRICULUM = {
    "levels": [
        {
            "level": 0,
            "name": "Fundamentos de IA",
            "duration_weeks": 4,
            "months": "1",
            "description": "Entenda o que é IA e como ela funciona",
            "learning_objectives": [
                "Compreender conceitos básicos de IA e Machine Learning",
                "Diferenciar tipos de IA (generativa, preditiva, etc)",
                "Identificar casos de uso de IA no dia a dia brasileiro",
                "Usar ChatGPT e Claude para tarefas básicas"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "O que é IA?",
                    "lessons": [
                        "História da IA: De Turing aos LLMs",
                        "Como funciona um modelo de linguagem",
                        "IA no Brasil: Casos de sucesso (Magazine Luiza, Nubank)"
                    ]
                },
                {
                    "module": 2,
                    "title": "Primeiros Passos com IA",
                    "lessons": [
                        "Criando conta no ChatGPT e Claude",
                        "Primeira conversa: Testando capacidades",
                        "IA como assistente pessoal"
                    ]
                }
            ],
            "project": "Usar IA para resolver um problema pessoal do dia a dia",
            "assessment": "Quiz de múltipla escolha + apresentação de caso de uso"
        },
        {
            "level": 1,
            "name": "Prompt Engineering Básico",
            "duration_weeks": 4,
            "months": "2",
            "description": "Aprenda a se comunicar efetivamente com IA",
            "learning_objectives": [
                "Escrever prompts claros e efetivos",
                "Usar técnicas de few-shot learning",
                "Iterar e refinar respostas da IA",
                "Aplicar IA em tarefas profissionais"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Arte de Fazer Perguntas",
                    "lessons": [
                        "Anatomia de um bom prompt",
                        "Contexto, instrução e formato",
                        "Erros comuns e como evitá-los"
                    ]
                },
                {
                    "module": 2,
                    "title": "Técnicas Avançadas",
                    "lessons": [
                        "Chain-of-thought prompting",
                        "Role prompting e personas",
                        "Templates de prompts para trabalho"
                    ]
                }
            ],
            "project": "Criar biblioteca de 20 prompts para seu trabalho",
            "assessment": "Avalição prática de qualidade de prompts"
        },
        {
            "level": 2,
            "name": "Ferramentas No-Code de IA",
            "duration_weeks": 8,
            "months": "3-4",
            "description": "Construa soluções sem programar",
            "learning_objectives": [
                "Usar Zapier/Make para automações",
                "Criar chatbots com plataformas no-code",
                "Integrar múltiplas ferramentas de IA",
                "Construir workflows automatizados"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Automação com Zapier/Make",
                    "lessons": [
                        "Introdução a automações (o que são triggers e actions)",
                        "Integrando ChatGPT com Google Sheets",
                        "Automatizando emails com IA",
                        "Workflows multi-step"
                    ]
                },
                {
                    "module": 2,
                    "title": "Chatbots e Assistentes",
                    "lessons": [
                        "Criando chatbot com Voiceflow",
                        "GPT personalizado no ChatGPT",
                        "Integrando com WhatsApp Business"
                    ]
                }
            ],
            "project": "Automatizar processo completo do seu trabalho",
            "assessment": "Apresentação de automação funcionando + ROI calculado"
        },
        {
            "level": 3,
            "name": "Dados e IA",
            "duration_weeks": 8,
            "months": "5-6",
            "description": "Use IA para análise e insights",
            "learning_objectives": [
                "Analisar dados com IA",
                "Criar dashboards automatizados",
                "Gerar insights de negócio",
                "Tomar decisões baseadas em dados"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Análise de Dados com IA",
                    "lessons": [
                        "Code Interpreter / Advanced Data Analysis",
                        "Limpeza e preparação de dados",
                        "Visualizações automáticas",
                        "Relatórios gerados por IA"
                    ]
                },
                {
                    "module": 2,
                    "title": "Business Intelligence com IA",
                    "lessons": [
                        "Conectando IA com bancos de dados",
                        "SQL gerado por IA",
                        "Dashboards inteligentes com Looker/Power BI + IA"
                    ]
                }
            ],
            "project": "Dashboard automatizado para seu negócio/trabalho",
            "assessment": "Apresentação de insights acionáveis"
        },
        {
            "level": 4,
            "name": "Introdução ao Low-Code",
            "duration_weeks": 12,
            "months": "7-9",
            "description": "Comece a codificar com assistência de IA",
            "learning_objectives": [
                "Entender lógica de programação básica",
                "Usar GitHub Copilot e Claude Code",
                "Modificar código existente",
                "Criar scripts simples"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Fundamentos de Programação",
                    "lessons": [
                        "Variáveis, loops e condicionais",
                        "Funções e estrutura de código",
                        "Python básico para automações",
                        "Lendo e entendendo código"
                    ]
                },
                {
                    "module": 2,
                    "title": "IA como Par de Programação",
                    "lessons": [
                        "GitHub Copilot: Seu copiloto de código",
                        "Claude Code e Cursor AI",
                        "Debugando com IA",
                        "Escrevendo testes com IA"
                    ]
                },
                {
                    "module": 3,
                    "title": "APIs e Integrações",
                    "lessons": [
                        "O que são APIs",
                        "Chamando APIs com Python",
                        "Autenticação e tokens",
                        "Integrando serviços externos"
                    ]
                }
            ],
            "project": "Script Python que automatiza tarefa complexa",
            "assessment": "Code review + apresentação do projeto"
        },
        {
            "level": 5,
            "name": "Construindo Web Apps",
            "duration_weeks": 12,
            "months": "10-12",
            "description": "Crie aplicações web completas",
            "learning_objectives": [
                "Construir interfaces com IA",
                "Conectar frontend e backend",
                "Hospedar aplicações na nuvem",
                "Gerenciar banco de dados"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Frontend com IA",
                    "lessons": [
                        "HTML, CSS, JavaScript básico",
                        "React/Next.js com Claude Code",
                        "Componentes e estado",
                        "UI/UX com IA generativa"
                    ]
                },
                {
                    "module": 2,
                    "title": "Backend e Banco de Dados",
                    "lessons": [
                        "Node.js ou Python Flask",
                        "APIs RESTful",
                        "PostgreSQL ou MongoDB",
                        "Autenticação de usuários"
                    ]
                },
                {
                    "module": 3,
                    "title": "Deploy e Hospedagem",
                    "lessons": [
                        "Vercel, Render, Railway",
                        "Variáveis de ambiente",
                        "Monitoramento e logs",
                        "CI/CD básico"
                    ]
                }
            ],
            "project": "Web app completo hospedado e funcional",
            "assessment": "Apresentação ao vivo + code review"
        },
        {
            "level": 6,
            "name": "IA Avançada e Fine-tuning",
            "duration_weeks": 8,
            "months": "13-14",
            "description": "Personalize modelos de IA",
            "learning_objectives": [
                "Entender arquitetura de LLMs",
                "Fine-tuning de modelos",
                "RAG (Retrieval Augmented Generation)",
                "Embeddings e busca semântica"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Além do Prompt",
                    "lessons": [
                        "Como LLMs realmente funcionam",
                        "Tokens, contexto e limites",
                        "Temperatura e outros parâmetros"
                    ]
                },
                {
                    "module": 2,
                    "title": "Customização de Modelos",
                    "lessons": [
                        "Fine-tuning com OpenAI",
                        "RAG com LangChain",
                        "Vetorização e ChromaDB/Pinecone",
                        "Criando assistente especializado"
                    ]
                }
            ],
            "project": "Assistente IA customizado para domínio específico",
            "assessment": "Demo técnica + documentação"
        },
        {
            "level": 7,
            "name": "Produto e Negócio",
            "duration_weeks": 12,
            "months": "15-17",
            "description": "Transforme sua aplicação em negócio",
            "learning_objectives": [
                "Product-market fit",
                "Monetização e precificação",
                "Marketing e aquisição",
                "Métricas e growth"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "De Projeto a Produto",
                    "lessons": [
                        "Validando sua ideia",
                        "MVP e iteração rápida",
                        "User research com IA",
                        "Roadmap de produto"
                    ]
                },
                {
                    "module": 2,
                    "title": "Go-to-Market",
                    "lessons": [
                        "Estratégias de precificação",
                        "Landing pages que convertem",
                        "SEO e marketing de conteúdo",
                        "Automação de vendas com IA"
                    ]
                },
                {
                    "module": 3,
                    "title": "Crescimento Sustentável",
                    "lessons": [
                        "Analytics e KPIs",
                        "Funis de conversão",
                        "Retenção de usuários",
                        "Suporte escalável com IA"
                    ]
                }
            ],
            "project": "Lançamento público com primeiros 10 usuários pagantes",
            "assessment": "Pitch de negócio + métricas reais"
        },
        {
            "level": 8,
            "name": "Scale & Mastery",
            "duration_weeks": 4,
            "months": "18",
            "description": "Escale seu negócio e se torne referência",
            "learning_objectives": [
                "Escalar infraestrutura",
                "Construir time",
                "Fundraising ou bootstrapping",
                "Comunidade e brand"
            ],
            "modules": [
                {
                    "module": 1,
                    "title": "Escalando Operações",
                    "lessons": [
                        "Infraestrutura de produção",
                        "Contratação e delegação",
                        "Processos e documentação",
                        "Legal e compliance"
                    ]
                },
                {
                    "module": 2,
                    "title": "Você como Builder Referência",
                    "lessons": [
                        "Personal brand",
                        "Compartilhando aprendizados",
                        "Mentoria e comunidade",
                        "Próximos passos da jornada"
                    ]
                }
            ],
            "project": "Case study completo da jornada",
            "assessment": "Apresentação final + certificação Cultura Builder"
        }
    ],
    "assessment_system": {
        "placement_test": {
            "sections": [
                {
                    "name": "Conhecimento de IA",
                    "questions": 10,
                    "topics": ["Conceitos básicos", "Ferramentas", "Casos de uso"]
                },
                {
                    "name": "Prompt Engineering",
                    "questions": 5,
                    "topics": ["Qualidade de prompts", "Iteração", "Contexto"]
                },
                {
                    "name": "Programação",
                    "questions": 10,
                    "topics": ["Lógica", "Leitura de código", "Debugging"]
                },
                {
                    "name": "Projeto Prático",
                    "type": "hands-on",
                    "task": "Resolver problema real com IA"
                }
            ],
            "scoring": {
                "0-30%": "Level 0 - Fundamentos",
                "31-45%": "Level 1-2 - Prompt Engineering",
                "46-60%": "Level 3 - Ferramentas No-Code",
                "61-75%": "Level 4-5 - Low-Code/Web Apps",
                "76-85%": "Level 6 - IA Avançada",
                "86-100%": "Level 7-8 - Produto e Scale"
            }
        }
    }
}


def get_curriculum():
    """Return full curriculum structure"""
    return CURRICULUM


def get_level(level_number: int):
    """Get specific level details"""
    for level in CURRICULUM["levels"]:
        if level["level"] == level_number:
            return level
    return None


def get_placement_test():
    """Get placement test structure"""
    return CURRICULUM["assessment_system"]["placement_test"]
