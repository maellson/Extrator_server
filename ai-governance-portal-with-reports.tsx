import { useState } from 'react';
import { ChevronDown, ChevronUp, Check, FileText, AlertTriangle, ClipboardList, ArrowRight } from 'lucide-react';

export default function EnhancedPortal() {
  const [expandedMenu, setExpandedMenu] = useState('caracterizacao');
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [showReport, setShowReport] = useState(false);
  const [reportType, setReportType] = useState('conformidade');
  
  const menuItems = [
    { id: 'caracterizacao', label: 'Caracterização', icon: '📋' },
    { id: 'governanca', label: 'Governança', icon: '⚙️' },
    { id: 'risco', label: 'Risco', icon: '⚠️' }
  ];
  
  const formQuestions = {
    caracterizacao: [
      {
        question: "Quais tipos de dados são utilizados pelo sistema?",
        options: [
          "Dados pessoais",
          "Dados sensíveis",
          "Dados corporativos",
          "Dados públicos"
        ],
        multiSelect: true
      },
      {
        question: "Quais áreas da organização serão impactadas?",
        options: [
          "Financeiro",
          "RH",
          "Marketing",
          "Operações",
          "TI"
        ],
        multiSelect: true
      },
      {
        question: "Quais são os objetivos do sistema de IA?",
        options: [
          "Automação de processos",
          "Análise preditiva",
          "Suporte à decisão",
          "Atendimento ao cliente"
        ],
        multiSelect: true
      }
    ],
    governanca: [
      {
        question: "Quem serão os responsáveis pela supervisão do sistema?",
        options: [
          "Comitê de ética",
          "Departamento de compliance",
          "Equipe técnica",
          "Gestores de negócio"
        ],
        multiSelect: true
      },
      {
        question: "Quais frameworks de governança serão adotados?",
        options: [
          "NIST AI Risk Management Framework",
          "EU AI Act",
          "ISO/IEC 42001",
          "Framework interno"
        ],
        multiSelect: true
      },
      {
        question: "Quais documentações serão mantidas?",
        options: [
          "Documentação técnica do modelo",
          "Registro de treinamento",
          "Logs de decisão",
          "Auditorias periódicas"
        ],
        multiSelect: true
      }
    ],
    risco: [
      {
        question: "Quais riscos foram identificados?",
        options: [
          "Viés e discriminação",
          "Privacidade e segurança de dados",
          "Transparência e explicabilidade",
          "Confiabilidade e robustez"
        ],
        multiSelect: true
      },
      {
        question: "Quais medidas de mitigação serão implementadas?",
        options: [
          "Testes de viés",
          "Revisão humana das decisões",
          "Monitoramento contínuo",
          "Anonimização de dados"
        ],
        multiSelect: true
      },
      {
        question: "Qual a classificação de impacto do sistema?",
        options: [
          "Alto impacto",
          "Médio impacto",
          "Baixo impacto",
          "Impacto mínimo"
        ],
        multiSelect: true
      }
    ]
  };
  
  // Análise das respostas para gerar os relatórios
  const generateReport = (type) => {
    // Verificar se todas as perguntas foram respondidas
    const allAnswered = Object.keys(formQuestions).every(menu => 
      formQuestions[menu].every((_, index) => 
        answers[`${menu}_${index}`] && answers[`${menu}_${index}`].length > 0
      )
    );
    
    if (!allAnswered) {
      return {
        title: "Avaliação incompleta",
        content: "Por favor, responda todas as perguntas para gerar um relatório completo.",
        recommendations: [],
        score: "N/A"
      };
    }
    
    // Análise específica baseada no tipo de relatório
    switch(type) {
      case 'conformidade':
        return generateConformidadeReport();
      case 'risco':
        return generateRiscoReport();
      case 'planoAcao':
        return generatePlanoAcaoReport();
      default:
        return {
          title: "Relatório não disponível",
          content: "O tipo de relatório selecionado não está disponível.",
          recommendations: [],
          score: "N/A"
        };
    }
  };
  
  const generateConformidadeReport = () => {
    // Verificar frameworks adotados
    const frameworks = answers['governanca_1'] || [];
    const documentacao = answers['governanca_2'] || [];
    const riscos = answers['risco_0'] || [];
    
    let conformidadeScore = 0;
    const maxScore = 10;
    let statusConformidade = "Não conforme";
    let recommendations = [];
    
    // Análise de conformidade baseada nas respostas
    if (frameworks.includes("EU AI Act") || frameworks.includes("NIST AI Risk Management Framework")) {
      conformidadeScore += 3;
    }
    
    if (documentacao.length >= 3) {
      conformidadeScore += 3;
    }
    
    if (answers['governanca_0']?.includes("Comitê de ética")) {
      conformidadeScore += 2;
    }
    
    if (answers['risco_1']?.includes("Revisão humana das decisões")) {
      conformidadeScore += 2;
    }
    
    // Determinar status baseado na pontuação
    if (conformidadeScore >= 8) {
      statusConformidade = "Alta conformidade";
    } else if (conformidadeScore >= 5) {
      statusConformidade = "Conformidade parcial";
    } else {
      statusConformidade = "Baixa conformidade";
    }
    
    // Gerar recomendações baseadas nas deficiências
    if (!frameworks.includes("EU AI Act") && answers['caracterizacao_0']?.includes("Dados pessoais")) {
      recommendations.push("Considerar a adoção do EU AI Act para sistemas que processam dados pessoais");
    }
    
    if (!documentacao.includes("Auditorias periódicas")) {
      recommendations.push("Implementar um programa de auditorias periódicas");
    }
    
    if (!answers['governanca_0']?.includes("Comitê de ética") && riscos.includes("Viés e discriminação")) {
      recommendations.push("Estabelecer um comitê de ética para supervisionar questões de viés");
    }
    
    return {
      title: "Relatório de Conformidade",
      content: `A análise de conformidade do sistema indica um nível de ${statusConformidade.toLowerCase()} (${conformidadeScore}/${maxScore}). ${
        conformidadeScore < 8 ? "São necessárias ações adicionais para aumentar a conformidade com as melhores práticas do setor." : 
        "O sistema demonstra boa aderência às práticas recomendadas de governança de IA."
      }`,
      recommendations: recommendations,
      score: `${conformidadeScore}/${maxScore} - ${statusConformidade}`
    };
  };
  
  const generateRiscoReport = () => {
    const riscos = answers['risco_0'] || [];
    const mitigacoes = answers['risco_1'] || [];
    const impacto = answers['risco_2'] || [];
    const dados = answers['caracterizacao_0'] || [];
    
    let riscoScore = 0;
    const maxScore = 10;
    let nivelRisco = "Alto";
    let recommendations = [];
    
    // Análise de risco baseada nas respostas
    if (riscos.length <= 2) {
      riscoScore += 2;
    }
    
    if (mitigacoes.length >= 3) {
      riscoScore += 3;
    }
    
    if (impacto.includes("Baixo impacto") || impacto.includes("Impacto mínimo")) {
      riscoScore += 3;
    } else if (impacto.includes("Médio impacto")) {
      riscoScore += 1;
    }
    
    if (!dados.includes("Dados sensíveis")) {
      riscoScore += 2;
    }
    
    // Determinar nível de risco baseado na pontuação
    if (riscoScore >= 8) {
      nivelRisco = "Baixo";
    } else if (riscoScore >= 5) {
      nivelRisco = "Médio";
    } else {
      nivelRisco = "Alto";
    }
    
    // Gerar recomendações
    if (riscos.includes("Viés e discriminação") && !mitigacoes.includes("Testes de viés")) {
      recommendations.push("Implementar testes de viés regulares");
    }
    
    if (riscos.includes("Privacidade e segurança de dados") && !mitigacoes.includes("Anonimização de dados")) {
      recommendations.push("Adotar técnicas de anonimização de dados");
    }
    
    if (!mitigacoes.includes("Monitoramento contínuo")) {
      recommendations.push("Estabelecer um sistema de monitoramento contínuo para detecção precoce de problemas");
    }
    
    if (impacto.includes("Alto impacto") && !answers['governanca_0']?.includes("Comitê de ética")) {
      recommendations.push("Para sistemas de alto impacto, estabelecer um comitê de ética dedicado");
    }
    
    return {
      title: "Relatório de Análise de Risco",
      content: `A análise indica que o sistema apresenta um nível de risco ${nivelRisco.toLowerCase()} (${riscoScore}/${maxScore}). ${
        nivelRisco === "Alto" ? "São necessárias medidas adicionais urgentes para mitigar os riscos identificados." :
        nivelRisco === "Médio" ? "Existem áreas de melhoria para reduzir ainda mais o perfil de risco." :
        "O sistema demonstra um bom controle sobre os riscos potenciais."
      }`,
      recommendations: recommendations,
      score: `${riscoScore}/${maxScore} - Risco ${nivelRisco}`
    };
  };
  
  const generatePlanoAcaoReport = () => {
    // Combinar recomendações dos relatórios de conformidade e risco
    const conformidadeRecs = generateConformidadeReport().recommendations;
    const riscoRecs = generateRiscoReport().recommendations;
    
    // Criar plano de ação consolidado
    const planoAcao = [...new Set([...conformidadeRecs, ...riscoRecs])].map((rec, index) => {
      // Determinar prioridade baseada no conteúdo da recomendação
      let prioridade = "Média";
      if (rec.includes("urgente") || rec.includes("Alto impacto") || rec.includes("estabelecer")) {
        prioridade = "Alta";
      } else if (rec.includes("considerar") || rec.includes("Baixo impacto")) {
        prioridade = "Baixa";
      }
      
      return {
        id: index + 1,
        acao: rec,
        prioridade: prioridade,
        responsavel: determinarResponsavel(rec),
        prazo: determinarPrazo(prioridade)
      };
    });
    
    return {
      title: "Plano de Ação",
      content: `Com base nas análises de conformidade e risco, foi desenvolvido um plano de ação com ${planoAcao.length} itens. ${
        planoAcao.filter(item => item.prioridade === "Alta").length > 0 ?
        `Existem ${planoAcao.filter(item => item.prioridade === "Alta").length} ações de alta prioridade que devem ser implementadas com urgência.` :
        "Não foram identificadas ações de alta prioridade."
      }`,
      recommendations: [],
      planoAcao: planoAcao
    };
  };
  
  const determinarResponsavel = (recomendacao) => {
    if (recomendacao.includes("ética") || recomendacao.includes("viés")) {
      return "Comitê de Ética";
    } else if (recomendacao.includes("dados") || recomendacao.includes("anonimização")) {
      return "Equipe de Segurança de Dados";
    } else if (recomendacao.includes("monitoramento") || recomendacao.includes("auditoria")) {
      return "Equipe de Governança de IA";
    } else if (recomendacao.includes("EU AI Act") || recomendacao.includes("conformidade")) {
      return "Departamento Jurídico";
    } else {
      return "Gestor do Projeto";
    }
  };
  
  const determinarPrazo = (prioridade) => {
    switch(prioridade) {
      case "Alta":
        return "30 dias";
      case "Média":
        return "60 dias";
      case "Baixa":
        return "90 dias";
      default:
        return "60 dias";
    }
  };
  
  const toggleMenu = (menuId) => {
    setExpandedMenu(menuId);
    setCurrentStep(0);
    setShowReport(false);
  };
  
  const handleAnswerSelect = (option) => {
    const currentKey = `${expandedMenu}_${currentStep}`;
    
    // Initialize if not exists
    if (!answers[currentKey]) {
      answers[currentKey] = [];
    }
    
    const updatedAnswers = { ...answers };
    
    // Toggle selection
    if (updatedAnswers[currentKey].includes(option)) {
      updatedAnswers[currentKey] = updatedAnswers[currentKey].filter(item => item !== option);
    } else {
      updatedAnswers[currentKey] = [...updatedAnswers[currentKey], option];
    }
    
    setAnswers(updatedAnswers);
  };
  
  const nextQuestion = () => {
    if (currentStep < formQuestions[expandedMenu].length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Find next menu
      const currentMenuIndex = menuItems.findIndex(item => item.id === expandedMenu);
      if (currentMenuIndex < menuItems.length - 1) {
        setExpandedMenu(menuItems[currentMenuIndex + 1].id);
        setCurrentStep(0);
      } else {
        // All questions completed, show report options
        setShowReport(true);
      }
    }
  };
  
  const previousQuestion = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else {
      // Find previous menu
      const currentMenuIndex = menuItems.findIndex(item => item.id === expandedMenu);
      if (currentMenuIndex > 0) {
        setExpandedMenu(menuItems[currentMenuIndex - 1].id);
        setCurrentStep(formQuestions[menuItems[currentMenuIndex - 1].id].length - 1);
      }
    }
  };
  
  const isOptionSelected = (option) => {
    const currentKey = `${expandedMenu}_${currentStep}`;
    return answers[currentKey]?.includes(option) || false;
  };
  
  const allQuestionsAnswered = () => {
    return Object.keys(formQuestions).every(menu => 
      formQuestions[menu].every((_, index) => 
        answers[`${menu}_${index}`] && answers[`${menu}_${index}`].length > 0
      )
    );
  };
  
  const handleViewReport = (type) => {
    setReportType(type);
    setShowReport(true);
  };
  
  const currentReport = generateReport(reportType);
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Menu Lateral */}
      <div className="w-64 bg-blue-700 text-white p-4 flex flex-col">
        <div className="text-xl font-bold mb-6">Portal de Governança de IA</div>
        
        {menuItems.map((item) => (
          <div 
            key={item.id}
            className={`flex items-center p-3 rounded cursor-pointer mb-2 ${
              expandedMenu === item.id ? 'bg-blue-800' : 'hover:bg-blue-600'
            }`}
            onClick={() => toggleMenu(item.id)}
          >
            <span className="mr-3 text-xl">{item.icon}</span>
            <span className="flex-grow">{item.label}</span>
            {expandedMenu === item.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        ))}
        
        {/* Opções de Relatório */}
        <div className="mt-8 border-t border-blue-600 pt-4">
          <div className="text-sm font-semibold mb-3 text-blue-200">RELATÓRIOS</div>
          
          <div 
            className={`flex items-center p-2 rounded cursor-pointer mb-2 ${
              showReport && reportType === 'conformidade' ? 'bg-blue-800' : 'hover:bg-blue-600'
            }`}
            onClick={() => handleViewReport('conformidade')}
          >
            <FileText size={18} className="mr-2" />
            <span>Conformidade</span>
          </div>
          
          <div 
            className={`flex items-center p-2 rounded cursor-pointer mb-2 ${
              showReport && reportType === 'risco' ? 'bg-blue-800' : 'hover:bg-blue-600'
            }`}
            onClick={() => handleViewReport('risco')}
          >
            <AlertTriangle size={18} className="mr-2" />
            <span>Análise de Risco</span>
          </div>
          
          <div 
            className={`flex items-center p-2 rounded cursor-pointer mb-2 ${
              showReport && reportType === 'planoAcao' ? 'bg-blue-800' : 'hover:bg-blue-600'
            }`}
            onClick={() => handleViewReport('planoAcao')}
          >
            <ClipboardList size={18} className="mr-2" />
            <span>Plano de Ação</span>
          </div>
        </div>
      </div>
      
      {/* Área de Conteúdo */}
      <div className="flex-grow p-6 overflow-y-auto">
        {!showReport ? (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-blue-700 mb-8">
              {menuItems.find(item => item.id === expandedMenu)?.label}
            </h2>
            
            {formQuestions[expandedMenu] && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold mb-6">
                  {formQuestions[expandedMenu][currentStep]?.question}
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  {formQuestions[expandedMenu][currentStep]?.options.map((option, index) => (
                    <div 
                      key={index}
                      className={`p-4 border-2 rounded-lg cursor-pointer ${
                        isOptionSelected(option) 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                      }`}
                      onClick={() => handleAnswerSelect(option)}
                    >
                      <div className="flex items-center justify-between">
                        <span>{option}</span>
                        {isOptionSelected(option) && (
                          <span className="bg-blue-500 text-white p-1 rounded-md">
                            <Check size={16} />
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Navegação */}
            <div className="flex justify-between items-center mt-10">
              <div className="text-sm text-gray-500">
                Pergunta {currentStep + 1} de {formQuestions[expandedMenu].length}
              </div>
              
              <div className="flex space-x-3">
                <button 
                  className="px-5 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                  onClick={previousQuestion}
                  disabled={expandedMenu === menuItems[0].id && currentStep === 0}
                >
                  Anterior
                </button>
                
                <button 
                  className="px-5 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  onClick={nextQuestion}
                >
                  {isLastQuestion() ? "Finalizar" : "Próxima"}
                </button>
              </div>
            </div>
            
            {/* Progresso */}
            <div className="mt-8">
              <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-blue-600 h-full rounded-full"
                  style={{ 
                    width: `${((menuItems.findIndex(item => item.id === expandedMenu) * formQuestions[expandedMenu].length + currentStep + 1) / 
                    (menuItems.length * 3)) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-blue-700">
                {currentReport.title}
              </h2>
              
              <button 
                className="px-4 py-2 text-blue-600 border border-blue-600 rounded hover:bg-blue-50"
                onClick={() => setShowReport(false)}
              >
                Voltar ao Questionário
              </button>
            </div>
            
            {!allQuestionsAnswered() ? (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md mb-6">
                <div className="flex items-center text-yellow-800">
                  <AlertTriangle size={20} className="mr-2" />
                  <span>Para um relatório completo, responda todas as perguntas do questionário.</span>
                </div>
              </div>
            ) : null}
            
            <div className="mb-6">
              <p className="text-gray-700">
                {currentReport.content}
              </p>
            </div>
            
            {reportType === 'planoAcao' ? (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">Ações Recomendadas:</h3>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white">
                    <thead>
                      <tr className="bg-gray-100 text-gray-600 uppercase text-sm leading-normal">
                        <th className="py-3 px-4 text-left">#</th>
                        <th className="py-3 px-4 text-left">Ação</th>
                        <th className="py-3 px-4 text-left">Prioridade</th>
                        <th className="py-3 px-4 text-left">Responsável</th>
                        <th className="py-3 px-4 text-left">Prazo</th>
                      </tr>
                    </thead>
                    <tbody className="text-gray-700 text-sm">
                      {currentReport.planoAcao && currentReport.planoAcao.map((item) => (
                        <tr key={item.id} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="py-3 px-4">{item.id}</td>
                          <td className="py-3 px-4">{item.acao}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              item.prioridade === 'Alta' ? 'bg-red-100 text-red-800' :
                              item.prioridade === 'Média' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {item.prioridade}
                            </span>
                          </td>
                          <td className="py-3 px-4">{item.responsavel}</td>
                          <td className="py-3 px-4">{item.prazo}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="mt-6">
                <div className="flex items-center mb-4">
                  <h3 className="text-lg font-semibold mr-3">Avaliação:</h3>
                  <span className={`px-3 py-1 rounded-full ${
                    currentReport.score.includes("Alta") || currentReport.score.includes("Baixo Risco") ? 
                    'bg-green-100 text-green-800' :
                    currentReport.score.includes("Baixa") || currentReport.score.includes("Alto Risco") ? 
                    'bg-red-100 text-red-800' : 
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {currentReport.score}
                  </span>
                </div>
                
                <h3 className="text-lg font-semibold mb-4">Recomendações:</h3>
                
                <ul className="space-y-3">
                  {currentReport.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <ArrowRight size={18} className="mr-2 mt-1 text-blue-500" />
                      <span>{rec}</span>
                    </li>
                  ))}
                  
                  {currentReport.recommendations.length === 0 && (
                    <li className="text-gray-500 italic">Não há recomendações adicionais.</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
  
  function isLastQuestion() {
    const isLastStep = currentStep === formQuestions[expandedMenu].length - 1;
    const isLastMenu = expandedMenu === menuItems[menuItems.length - 1].id;
    return isLastStep && isLastMenu;
  }
}
