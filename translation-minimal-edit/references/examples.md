# 案例集

以下为真实执行案例，展示如何对齐中英改动并对应修改小语种（德/法/西/俄），保持 minimal changes。

---

## 案例1：泳装礼包标题（去emoji + Ultimate→Deluxe）

### 改动分析

| 位置 | 原始 | 新 | 同步？ |
|---|---|---|---|
| 开头 | 🎁 | （无） | ✅ 全部去emoji |
| 中文语气 | 趁现在**！** | 趁现在**~** | ❌ 小语种未译"趁现在"，无对应 |
| 英文礼包等级 | **the Ultimate** | **Deluxe** | ✅ 德法西同步；俄语保留原译（用户指定） |

### 各语言修改结果

**德语**
- 原始：`🎁 [Nur für kurze Zeit] Zankous neues Bade-Outfit „Glühender Lavendel" und das ultimative Rückkehr-Geschenkpaket`
- 修改后：`[Nur für kurze Zeit] Zankous neues Bade-Outfit „Glühender Lavendel" und das Deluxe-Rückkehr-Geschenkpaket`
- 改动：去🎁；`ultimative`→`Deluxe`；定冠词`das`保留

**法语**
- 原始：`🎁 [Durée limitée] Nouveau maillot de bain de Zankou « Lavande brûlante » et pack cadeau de retour ultime`
- 修改后：`[Durée limitée] Nouveau maillot de bain de Zankou « Lavande brûlante » et pack cadeau de retour Deluxe`
- 改动：去🎁；`ultime`→`Deluxe`（后置定语位置不变）

**西班牙语**
- 原始：`🎁 [Tiempo limitado] Nuevo traje de baño de Zankou "Lavanda abrasadora" y el Paquete de regalo de bienvenida definitivo`
- 修改后：`[Tiempo limitado] Nuevo traje de baño de Zankou "Lavanda abrasadora" y el Paquete de regalo de bienvenida Deluxe`
- 改动：去🎁；`definitivo`→`Deluxe`

**俄语**
- 原始：`🎁 (Ограниченное время) Новый купальник Занку «Обжигающая лаванда» и подарочный супернабор «С возвращением!»`
- 修改后：`(Ограниченное время) Новый купальник Занку «Обжигающая лаванда» и подарочный супернабор «С возвращением!»`
- 改动：仅去🎁；`супернабор`保留不改Deluxe（用户指定俄语保留原译）

### 关键判断
- 英文去`the`不同步到小语种定冠词（德语`das`、西语`el`保留）
- 俄语原译用`супернабор`而非ultimate直译名，用户决定保留，不强行改Deluxe

---

## 案例2：兑换码邮件（去"签到"）

### 改动分析

| 位置 | 原始 | 新 | 同步？ |
|---|---|---|---|
| 领取方式 | **签到**最高可领取 / **Check in for** | 最高可领取 / **Get** | ✅ 全部去签到表达 |
| 中文标点 | 敬请期待**！** | 敬请期待**。** | ❌ 小语种未独立译"敬请期待"，无对应 |

### 各语言修改结果

**德语**
- 原始：`Melde dich an und erhalte bis zu Annulith ×640 + Zinkwürfel ×2!`
- 修改后：`Erhalte bis zu Annulith ×640 + Zinkwürfel ×2!`
- 改动：`Melde dich an und erhalte`→`Erhalte`（去"签到"，首字母大写因句首）

**法语**
- 原始：`Validez votre passage pour obtenir jusqu'à Annulith ×640 + Dé confectionné ×2 !`
- 修改后：`Obtenez jusqu'à Annulith ×640 + Dé confectionné ×2 !`
- 改动：`Validez votre passage pour obtenir`→`Obtenez`（去"签到/验证通行"，改敬语命令式）

**西班牙语**
- 原始：`¡Inicia sesión para conseguir hasta Arolitas × 640 + Dados fabricados × 2!`
- 修改后：`¡Consigue hasta Arolitas × 640 + Dados fabricados × 2!`
- 改动：`Inicia sesión para conseguir`→`Consigue`（去"登录"，改tú命令式）

**俄语**
- 原始：`Отмечайтесь в игре и получите до 640 аннулитов и «Шулерский кубик» ×2!`
- 修改后：`Получите до 640 аннулитов и «Шулерский кубик» ×2!`
- 改动：`Отмечайтесь в игре и получите`→`Получите`（去"在游戏中签到"）

---

## 案例3：组合活动文案（标点+去签到+Ultimate→Deluxe，英文句式重构不同步）

### 改动分析

| 改动 | 中文 | 英文 | 小语种同步？ |
|---|---|---|---|
| 开头标点 | 趁现在**！**→趁现在**，** | `:`→`,` | ✅ 同步 |
| 礼包后标点 | 回归礼包**！**→回归礼包**，** | `!`→`.` | ✅ 同步为逗号 |
| 去签到 | **签到**最高可→最高可 | **Check in for**→**Get** | ✅ 全部同步 |
| Ultimate→Deluxe | （中文未变） | **Ultimate**→**Deluxe** | ✅ 德法西同步；俄语保留 |
| 句式重构/加词 | （中文无对应） | 加unlock, exclusive, claim your | ❌ 不同步，属英文本地化润色 |

### 各语言修改结果

**德语**
- 原始：`Nur für kurze Zeit: Zankous Bade-Outfit„Glühender Lavendel" & das ultimative Rückkehr-Geschenkpaket! Schau rein und erhalte bis zu Annulith ×640 + Zinkwürfel ×2!`
- 修改后：`Nur für kurze Zeit, Zankous Bade-Outfit„Glühender Lavendel" & das Deluxe-Rückkehr-Geschenkpaket, Erhalte bis zu Annulith ×640 + Zinkwürfel ×2!`
- 改动：`:`→`,`；`ultimative`→`Deluxe`；`paket! Schau rein und erhalte`→`paket, Erhalte`

**法语**
- 原始：`Pendant une durée limitée : Maillot de bain de Zankou « Lavande brûlante » et pack cadeau de retour ultime ! Validez votre passage pour obtenir jusqu'à Annulith ×640 + Dé confectionné ×2 !`
- 修改后：`Pendant une durée limitée, Maillot de bain de Zankou « Lavande brûlante » et pack cadeau de retour Deluxe, Obtenez jusqu'à Annulith ×640 + Dé confectionné ×2 !`
- 改动：`limitée :`→`limitée,`；`ultime !`→`Deluxe,`；`Validez votre passage pour obtenir`→`Obtenez`

**西班牙语**
- 原始：`Por tiempo limitado: ¡traje de baño de Zankou "Lavanda abrasadora" y el Paquete de regalo de bienvenida definitivo! ¡Inicia sesión para conseguir hasta Arolitas × 640 + Dados fabricados × 2!`
- 修改后：`Por tiempo limitado, traje de baño de Zankou "Lavanda abrasadora" y el Paquete de regalo de bienvenida Deluxe, ¡Consigue hasta Arolitas × 640 + Dados fabricados × 2!`
- 改动：`limitado: ¡traje`→`limitado, traje`（去冒号和倒叹号）；`definitivo!`→`Deluxe,`；`¡Inicia sesión para conseguir`→`¡Consigue`

**俄语**
- 原始：`Только в течение ограниченного времени: новый купальник Занку «Обжигающая лаванда» и подарочный супернабор «С возвращением!». Отмечайтесь в игре и получите до 640 аннулитов и «Шулерский кубик» ×2!`
- 修改后：`Только в течение ограниченного времени, новый купальник Занку «Обжигающая лаванда» и подарочный супернабор «С возвращением!», получите до 640 аннулитов и «Шулерский кубик» ×2!`
- 改动：`времени:`→`времени,`；`«С возвращением!». Отмечайтесь в игре и получите`→`«С возвращением!», получите`；`супернабор`保留

### 关键判断
- 英文第一句几乎重写（unlock Zankou's exclusive... and claim your Deluxe...），但中文只是标点+去签到，因此小语种**不跟随英文重写**，只做对应中文的最小改动
- 西语倒感叹号`¡`在去掉感叹号时要成对去掉（开头`¡`和结尾`!`都去掉）

---

## 案例4：签到奖励列表（奖励项删减改"等其他奖励"）

### 改动分析

**第一句（登录奖励）：**
- 原始：环石×200，方斯×10000，特级猎人攻略×5 / Annulith x200, Fons x10,000 and Elite Hunter Guide x5
- 新：环石×200 / Annulith x200
- 改动：删方斯×10000、特级猎人攻略×5

**第二句（签到+鉴定任务奖励）：**
- 原始：…方斯×370000，去噪底液×2 / …Fons x370,000 and De-noise Solution x2
- 新：…方斯等其他奖励 / …Fons, and more
- 改动：删方斯具体数字、删去噪底液，改"等其他奖励"

**签到表达：** 小语种原有的签到/登录表达（Connectez-vous / Inicia sesión / Отмечайтесь / Schau rein）保留，**不强行改成英文Check-In**。

### 各语言修改结果

**德语**
- 原始第一句：`Melde dich an und erhalte Annulith ×200, Fons ×10.000 und Guide für Elite-Jäger ×5.`
- 修改后：`Melde dich an und erhalte Annulith ×200.`
- 原始第二句：`Schau rein, schließe Gutachten-Missionen ab, und erhalte bis zu Annulith ×640, Zinkwürfel ×2, Fons ×370.000 und Anti-Rausch-Lösung ×2.`
- 修改后：`Schau rein, schließe Gutachten-Missionen ab, und erhalte bis zu Annulith ×640, Zinkwürfel ×2, Fons und weitere Belohnungen.`
- 改动：第一句删多余奖励；第二句删`Fons ×370.000`数字和`Anti-Rausch-Lösung ×2`，改`Fons und weitere Belohnungen`；动词部分完全保留

**法语**
- 原始第一句：`Connectez-vous pour obtenir Annulith ×200, Fons ×10 000 et Guide de chasseur d'élite ×5.`
- 修改后：`Connectez-vous pour obtenir Annulith ×200.`
- 原始第二句：`Connectez-vous et terminez les Quêtes d'évaluation pour obtenir jusqu'à Annulith ×640, Dé confectionné ×2, Fons ×370 000 et Solution antibruit ×2.`
- 修改后：`Connectez-vous et terminez les Quêtes d'évaluation pour obtenir jusqu'à Annulith ×640, Dé confectionné ×2, Fons et d'autres récompenses.`
- 改动：第一句删多余奖励；第二句删`Fons ×370 000`数字和`Solution antibruit ×2`，改`Fons et d'autres récompenses`

**西班牙语**
- 原始第一句：`Inicia sesión para conseguir Arolitas × 200, Fons × 10 000 y Guías de caza élite × 5.`
- 修改后：`Inicia sesión para conseguir Arolitas × 200.`
- 原始第二句：`Inicia sesión y completa las Misiones de peritaje para conseguir hasta Arolitas × 640, Dados fabricados × 2, Fons × 370 000 y Soluciones antirruido × 2.`
- 修改后：`Inicia sesión y completa las Misiones de peritaje para conseguir hasta Arolitas × 640, Dados fabricados × 2, Fons y más recompensas.`
- 改动：第一句删多余奖励；第二句删`Fons × 370 000`数字和`Soluciones antirruido × 2`，改`Fons y más recompensas`

**俄语**
- 原始第一句：`Войдите в игру, чтобы получить: «Аннулит» ×200, «Фонс» ×10 000 и «Руководство элитного охотника» ×5.`
- 修改后：`Войдите в игру, чтобы получить: «Аннулит» ×200.`
- 原始第二句：`Отмечайтесь и выполняйте миссии оценки, чтобы получить до 640 аннулитов, «Шулерский кубик» ×2, «Фонс» ×370 000 и «Устранитель шума» ×2.`
- 修改后：`Отмечайтесь и выполняйте миссии оценки, чтобы получить до 640 аннулитов, «Шулерский кубик» ×2, «Фонс» и другие награды.`
- 改动：第一句删多余奖励（冒号保留）；第二句删`«Фонс» ×370 000`数字和`«Устранитель шума» ×2`，改`«Фонс» и другие награды`；动词结构保留

### 关键判断
- 英文第二句把"Check in and complete"改为"Complete Check-In and"（语序合并），但小语种**不强行合并**，保留原有的双动词结构（如俄语`Отмечайтесь и выполняйте`天然对应"签到+完成"，无需改）
- "等其他奖励"各语言译法：德`und weitere Belohnungen`、法`et d'autres récompenses`、西`y más recompensas`、俄`и другие награды`

---

## 案例5：角色介绍（删身份背景句+合并主谓）

### 改动分析

- 原始中文：作为「红字」地位最高的成员，**残虹T女士最锋利的一把刀，也是最危险的一个女儿。**她可以进入隐身状态…
- 新中文：作为「红字」地位最高的成员，她可以进入隐身状态…
- 原始英文：As the highest-ranking member of The Scarlet Letter, Zankou **is Madam T's sharpest blade and her most dangerous daughter. She** can turn invisible…
- 新英文：…Zankou can turn invisible…
- 改动：删身份描述句（"最锋利的刀/武器 + 最危险的女儿"），把前后句的主语和谓语合并

### 各语言修改结果

**德语**
- 原始：`Als ranghöchstes Mitglied von „Der scharlachrote Buchstabe" ist Zankou die schärfste Waffe von Frau T – und auch ihre gefährlichste Tochter. Sie kann sich unsichtbar machen…`
- 修改后：`Als ranghöchstes Mitglied von „Der scharlachrote Buchstabe" kann Zankou sich unsichtbar machen…`
- 改动：删`ist Zankou die schärfste Waffe von Frau T – und auch ihre gefährlichste Tochter. Sie`，合并为`kann Zankou`

**法语**
- 原始：`En tant que membre le mieux classé de La Lettre écarlate, Zankou est la lame la plus acérée de Madame T et sa fille la plus redoutable. Elle peut se rendre invisible…`
- 修改后：`En tant que membre le mieux classé de La Lettre écarlate, Zankou peut se rendre invisible…`
- 改动：删`est la lame la plus acérée de Madame T et sa fille la plus redoutable. Elle`，合并为`Zankou peut`

**西班牙语**
- 原始：`Como miembro de mayor rango de La Letra Escarlata, Zankou es la espada más afilada de la Señora T y su hija más peligrosa. Puede volverse invisible…`
- 修改后：`Como miembro de mayor rango de La Letra Escarlata, Zankou puede volverse invisible…`
- 改动：删`es la espada más afilada de la Señora T y su hija más peligrosa.`，后句`Puede`补上主语合并为`Zankou puede`

**俄语**
- 原始：`Будучи высокопоставленным членом организации «Алый символ», Занку — это самый острый клинок и самая опасная дочь госпожи Т. Она способна становиться невидимой…`
- 修改后：`Будучи высокопоставленным членом организации «Алый символ», Занку способна становиться невидимой…`
- 改动：删`— это самый острый клинок и самая опасная дочь госпожи Т. Она`，合并为`Занку способна`

### 关键判断
- 删句后必须检查语法衔接：西语原句后段省略主语`Puede`，删句后需补上主语`Zankou puede`
- 俄语`— это`结构删去后，主语`Занку`直接接谓语`способна`，语法通顺
