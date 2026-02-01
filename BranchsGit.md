Estratégia de Branches (Git Flow)
Para manter a organização, use uma estratégia de branches bem definida. A mais famosa é o Git Flow:

main (ou master): Representa o código que está em produção. Esta branch só recebe código de branches de release ou hotfix. Cada commit na main deve ter uma tag de versão.

develop: É a branch de integração principal. Todo o desenvolvimento de novas funcionalidades acontece aqui. Ela representa o "próximo lançamento".

feature/*: Você cria uma branch a partir de develop para cada nova funcionalidade (ex: feature/grafico-estatisticas). Quando termina, você a mescla de volta em develop.

release/*: Quando develop está pronta para um novo lançamento, você cria uma branch release/v1.5.0. Nela, você só faz testes finais e pequenas correções. Quando está estável, você a mescla em main (e cria a tag) e também de volta em develop.

hotfix/*: Para bugs urgentes em produção. Você cria a branch a partir de main, corrige o bug, mescla de volta em main (e cria uma tag de patch, ex: v1.4.3) e também em develop.