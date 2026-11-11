-- Eventos que mudam o patamar de vendas (seção 17). Levantamento ainda incompleto:
-- faltam, por exemplo, os retrofits de Coloninha e Santa Terezinha (Gaspar).
INSERT INTO apoio.evento_loja (idvarejista, loja_nome, data_evento, precisao_data, tipo, descricao, fonte) VALUES
  ('redetop-indaial-sc', 'Rede TOP Penha',                   '2026-07-21', 'dia',          'inauguracao',   'Nova unidade inaugurada',                       'SuperVarejo'),
  ('redetop-indaial-sc', 'Rede TOP Presidente Getúlio',      '2026-05-01', 'mes',          'reinauguracao', 'Reinauguração após retrofit',                   'SuperVarejo'),
  ('redetop-indaial-sc', 'Rede TOP Porto Belo',              NULL,         'desconhecida', 'obra',          'Loja em obra, inauguração prevista para 2026',  'NSC Total'),
  ('redetop-indaial-sc', 'Rede TOP Bela Vista (Gaspar)',     '2025-05-08', 'dia',          'inauguracao',   'Série de cerca de 18 meses no piloto',          'SuperVarejo'),
  ('redetop-indaial-sc', 'Rede TOP Blumenau General Osório', '2024-09-26', 'dia',          'reinauguracao', 'Formato menor, de conveniência',                'SuperVarejo')
ON CONFLICT DO NOTHING;
