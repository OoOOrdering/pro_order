-- psql -U postgres -d oz_project -f query.sql

INSERT INTO idol_idol (name, en_name, debut_date, agency, description, profile_image, created_at, updated_at, is_active)
VALUES
('뉴진스', 'NewJeans', '2022-07-22', 'ADOR', '하입보이~', NULL, NOW(), NOW(), TRUE),
('르세라핌', 'LE SSERAFIM', '2022-05-02', 'Source Music', '세상에 맞서 당당히', NULL, NOW(), NOW(), TRUE),
('아이브', 'IVE', '2021-12-01', 'Starship Entertainment', '완성형 그룹', NULL, NOW(), NOW(), TRUE),
('에스파', 'aespa', '2020-11-17', 'SM Entertainment', 'AI 아바타 컨셉', NULL, NOW(), NOW(), TRUE),
('스테이씨', 'STAYC', '2020-11-12', 'High Up Entertainment', '수민 최고', NULL, NOW(), NOW(), TRUE),
('있지', 'ITZY', '2019-02-12', 'JYP Entertainment', '걸크러시의 정석', NULL, NOW(), NOW(), TRUE),
('트와이스', 'TWICE', '2015-10-20', 'JYP Entertainment', '원스 사랑해', NULL, NOW(), NOW(), TRUE),
('레드벨벳', 'Red Velvet', '2014-08-01', 'SM Entertainment', '레드와 벨벳의 조화', NULL, NOW(), NOW(), TRUE),
('블랙핑크', 'BLACKPINK', '2016-08-08', 'YG Entertainment', '세계적인 K-POP 스타', NULL, NOW(), NOW(), TRUE),
('마마무', 'MAMAMOO', '2014-06-19', 'RBW', '실력파 걸그룹', NULL, NOW(), NOW(), TRUE),
('소녀시대', 'Girls Generation', '2007-08-05', 'SM Entertainment', '국민 걸그룹', NULL, NOW(), NOW(), TRUE),
('카라', 'KARA', '2007-03-29', 'DSP Media', '2세대 대표 걸그룹', NULL, NOW(), NOW(), TRUE),
('씨스타', 'SISTAR', '2010-06-03', 'Starship Entertainment', '썸머 퀸', NULL, NOW(), NOW(), TRUE),
('러블리즈', 'Lovelyz', '2014-11-12', 'Woollim Entertainment', '청순돌', NULL, NOW(), NOW(), TRUE),
('오마이걸', 'OH MY GIRL', '2015-04-21', 'WM Entertainment', '콘셉트 요정', NULL, NOW(), NOW(), TRUE),
('드림캐쳐', 'Dreamcatcher', '2017-01-13', 'Dreamcatcher Company', '록 컨셉 독보적', NULL, NOW(), NOW(), TRUE),
('우주소녀', 'WJSN', '2016-02-25', 'Starship Entertainment', '우주처럼 다양한 매력', NULL, NOW(), NOW(), TRUE),
('이달의 소녀', 'LOONA', '2018-08-20', 'Blockberry Creative', '개별 데뷔 후 단체', NULL, NOW(), NOW(), TRUE),
('(여자)아이들', '(G)I-DLE', '2018-05-02', 'CUBE Entertainment', '자체 프로듀싱', NULL, NOW(), NOW(), TRUE),
('에버글로우', 'EVERGLOW', '2019-03-18', 'Yuehua Entertainment', '파워풀 퍼포먼스', NULL, NOW(), NOW(), TRUE);
