在我的golang dependency update项目中，我进行了大量测试，总结出了prompt engineering的几个关键点。
1. AI prefers narrative texts as inputs rather than structured json
2. Intention is necessary, or it will output unrelated contents
3. Use advanced functions to @context, or it won’t identify similar function names 
4. State both of old and new signatures, or it cannot handle removed args
5. Tell AI to fill additional args using initialized values, or fake contents will appear
6. Restrict the output format using examples, or it will output unnecessary contents

