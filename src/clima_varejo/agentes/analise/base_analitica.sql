-- Base analítica: cada venda por hora cruzada com o clima do mesmo horário e local.
-- Lê só as tabelas do contrato. Cada variável vem do ponto mapeado para ela (ou 'todas').
WITH ponto AS (
    SELECT idvarejista, idloja, variavel, id_ponto, fonte
    FROM contrato.loja_ponto
)
SELECT
    v.idvarejista, v.idloja, v.data_hora_local, v.idproduto,
    v.quantidade, v.valor_bruto, v.valor_desconto, v.n_cupons,
    t.temperatura_c,
    p.precipitacao_mm,
    r.radiacao_w_m2
FROM contrato.vendas_hora v
LEFT JOIN ponto pt ON pt.idvarejista = v.idvarejista AND pt.idloja = v.idloja AND pt.variavel IN ('temperatura_c', 'todas')
LEFT JOIN contrato.clima_hora t ON t.id_ponto = pt.id_ponto AND t.fonte = pt.fonte AND t.data_hora_local = v.data_hora_local
LEFT JOIN ponto pp ON pp.idvarejista = v.idvarejista AND pp.idloja = v.idloja AND pp.variavel IN ('precipitacao_mm', 'todas')
LEFT JOIN contrato.clima_hora p ON p.id_ponto = pp.id_ponto AND p.fonte = pp.fonte AND p.data_hora_local = v.data_hora_local
LEFT JOIN ponto pr ON pr.idvarejista = v.idvarejista AND pr.idloja = v.idloja AND pr.variavel IN ('radiacao_w_m2', 'todas')
LEFT JOIN contrato.clima_hora r ON r.id_ponto = pr.id_ponto AND r.fonte = pr.fonte AND r.data_hora_local = v.data_hora_local
WHERE v.data_hora_local >= %(inicio)s AND v.data_hora_local < %(fim)s;
