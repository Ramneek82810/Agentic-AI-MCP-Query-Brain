CREATE TABLE IF NOT EXISTS user_vendor_info (
  user_id INT PRIMARY KEY,
  user_name VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  vendor_id VARCHAR(100),
  vendor_name VARCHAR(150) NOT NULL,
  vendor_status VARCHAR(50) CHECK (
    vendor_status IN ('active', 'inactive', 'pending')
  ),
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);INSERT INTO
  user_vendor_info (
    user_id,
    user_name,
    email,
    vendor_id,
    vendor_name,
    vendor_status,
    last_updated
  )
VALUES
  (
    4821,
    'Alice Walker',
    'alice.walker@example.com',
    'VN-7392',
    'BrightPath Solutions',
    'active',
    NOW() - INTERVAL '3 days'
  ),
  (
    9274,
    'James Carter',
    'james.carter@example.com',
    'VN-4821',
    'NorthGate Traders',
    'inactive',
    NOW() - INTERVAL '12 hours'
  ),
  (
    3157,
    'Sophia Mitchell',
    'sophia.mitchell@example.com',
    'VN-9248',
    'Skyline Ventures',
    'pending',
    NOW() - INTERVAL '7 days'
  ),
  (
    6082,
    'Daniel Foster',
    'daniel.foster@example.com',
    'VN-1037',
    'Everest Supplies',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    7419,
    'Olivia Bennett',
    'olivia.bennett@example.com',
    'VN-7754',
    'SilverLeaf Corp',
    'inactive',
    NOW() - INTERVAL '18 hours'
  ),
  (
    5638,
    'William Turner',
    'william.turner@example.com',
    'VN-3390',
    'Summit Dynamics',
    'pending',
    NOW() - INTERVAL '4 days'
  ),
  (
    8920,
    'Emma Collins',
    'emma.collins@example.com',
    'VN-6551',
    'BlueHorizon Group',
    'active',
    NOW() - INTERVAL '6 hours'
  ),
  (
    4765,
    'Henry Reed',
    'henry.reed@example.com',
    'VN-9207',
    'CrownPoint Logistics',
    'inactive',
    NOW() - INTERVAL '10 days'
  ),
  (
    3492,
    'Ava Morgan',
    'ava.morgan@example.com',
    'VN-1184',
    'Pinnacle Retailers',
    'active',
    NOW() - INTERVAL '1 day'
  ),
  (
    5108,
    'Lucas Price',
    'lucas.price@example.com',
    'VN-4472',
    'BrightWave Partners',
    'pending',
    NOW() - INTERVAL '5 days'
  ),
  (
    7841,
    'Isabella Cooper',
    'isabella.cooper@example.com',
    'VN-5529',
    'GoldenGate Systems',
    'active',
    NOW() - INTERVAL '22 hours'
  ),
  (
    6397,
    'Mason Brooks',
    'mason.brooks@example.com',
    'VN-7710',
    'Lighthouse Consulting',
    'inactive',
    NOW() - INTERVAL '15 days'
  ),
  (
    9002,
    'Mia Hayes',
    'mia.hayes@example.com',
    'VN-6158',
    'HarborEdge Technologies',
    'active',
    NOW() - INTERVAL '9 hours'
  ),
  (
    4286,
    'Ethan Ward',
    'ethan.ward@example.com',
    'VN-8093',
    'IronPeak Enterprises',
    'pending',
    NOW() - INTERVAL '2 days'
  ),
  (
    3751,
    'Charlotte King',
    'charlotte.king@example.com',
    'VN-9402',
    'RedStone Innovations',
    'active',
    NOW() - INTERVAL '4 hours'
  ),
  (
    6920,
    'Benjamin Scott',
    'benjamin.scott@example.com',
    'VN-3075',
    'RiverView Global',
    'inactive',
    NOW() - INTERVAL '11 days'
  ),
  (
    5217,
    'Amelia Phillips',
    'amelia.phillips@example.com',
    'VN-8462',
    'ClearPath Solutions',
    'active',
    NOW() - INTERVAL '1 day'
  ),
  (
    8304,
    'Elijah Morris',
    'elijah.morris@example.com',
    'VN-1098',
    'SummitWave Ltd',
    'pending',
    NOW() - INTERVAL '13 hours'
  ),
  (
    4789,
    'Harper Rogers',
    'harper.rogers@example.com',
    'VN-6743',
    'VisionPoint Group',
    'inactive',
    NOW() - INTERVAL '3 days'
  ),
  (
    6892,
    'Alexander Gray',
    'alexander.gray@example.com',
    'VN-2307',
    'NextPhase Inc',
    'active',
    NOW() - INTERVAL '16 hours'
  ),
  (
    9156,
    'Evelyn Jenkins',
    'evelyn.jenkins@example.com',
    'VN-7731',
    'BrightStone Retail',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    3047,
    'Michael Adams',
    'michael.adams@example.com',
    'VN-6670',
    'HighTower Associates',
    'inactive',
    NOW() - INTERVAL '6 days'
  ),
  (
    7091,
    'Abigail Ross',
    'abigail.ross@example.com',
    'VN-5492',
    'NorthBridge Solutions',
    'active',
    NOW() - INTERVAL '19 hours'
  ),
  (
    4526,
    'Sebastian Kelly',
    'sebastian.kelly@example.com',
    'VN-9124',
    'CrestPoint Logistics',
    'pending',
    NOW() - INTERVAL '2 days'
  ),
  (
    8065,
    'Ella Howard',
    'ella.howard@example.com',
    'VN-2859',
    'IronBridge Partners',
    'active',
    NOW() - INTERVAL '4 days'
  ),
  (
    9238,
    'Jack Peterson',
    'jack.peterson@example.com',
    'VN-3820',
    'PeakPoint Supplies',
    'inactive',
    NOW() - INTERVAL '7 days'
  ),
  (
    5179,
    'Lily Ramirez',
    'lily.ramirez@example.com',
    'VN-7081',
    'SilverCrest Dynamics',
    'active',
    NOW() - INTERVAL '5 hours'
  ),
  (
    3642,
    'Owen Cooper',
    'owen.cooper@example.com',
    'VN-9345',
    'BluePeak Enterprises',
    'pending',
    NOW() - INTERVAL '9 days'
  ),
  (
    6029,
    'Grace Stewart',
    'grace.stewart@example.com',
    'VN-6129',
    'SummitGate Retail',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    7481,
    'Matthew Hughes',
    'matthew.hughes@example.com',
    'VN-7214',
    'ClearWave Tech',
    'inactive',
    NOW() - INTERVAL '14 hours'
  ),
  (
    8957,
    'Chloe Bryant',
    'chloe.bryant@example.com',
    'VN-5189',
    'CrownWave Solutions',
    'active',
    NOW() - INTERVAL '3 days'
  ),
  (
    3819,
    'Jacob Rivera',
    'jacob.rivera@example.com',
    'VN-2360',
    'NorthStone Ventures',
    'pending',
    NOW() - INTERVAL '11 days'
  ),
  (
    5603,
    'Zoe Russell',
    'zoe.russell@example.com',
    'VN-9503',
    'IronClad Logistics',
    'active',
    NOW() - INTERVAL '1 day'
  ),
  (
    6348,
    'Carter Jenkins',
    'carter.jenkins@example.com',
    'VN-6721',
    'Evergreen Dynamics',
    'inactive',
    NOW() - INTERVAL '20 hours'
  ),
  (
    7194,
    'Ella Simmons',
    'ella.simmons@example.com',
    'VN-4856',
    'Visionary Global',
    'active',
    NOW() - INTERVAL '7 days'
  ),
  (
    8923,
    'Noah Long',
    'noah.long@example.com',
    'VN-9472',
    'BrightWave Retailers',
    'pending',
    NOW() - INTERVAL '4 days'
  ),
  (
    5037,
    'Scarlett Fisher',
    'scarlett.fisher@example.com',
    'VN-3794',
    'SummitBridge Consulting',
    'active',
    NOW() - INTERVAL '10 hours'
  ),
  (
    6402,
    'Logan Hayes',
    'logan.hayes@example.com',
    'VN-1593',
    'ClearStone Ltd',
    'inactive',
    NOW() - INTERVAL '8 days'
  ),
  (
    7321,
    'Victoria Powell',
    'victoria.powell@example.com',
    'VN-8035',
    'IronWave Enterprises',
    'active',
    NOW() - INTERVAL '15 hours'
  ),
  (
    8460,
    'Jackson Perry',
    'jackson.perry@example.com',
    'VN-6817',
    'PeakGate Systems',
    'pending',
    NOW() - INTERVAL '3 days'
  ),
  (
    9118,
    'Avery Price',
    'avery.price@example.com',
    'VN-2237',
    'BrightBridge Corp',
    'active',
    NOW() - INTERVAL '6 days'
  ),
  (
    4792,
    'David Edwards',
    'david.edwards@example.com',
    'VN-9306',
    'CrownEdge Partners',
    'inactive',
    NOW() - INTERVAL '2 days'
  ),
  (
    3557,
    'Madison Bennett',
    'madison.bennett@example.com',
    'VN-7824',
    'NextWave Technologies',
    'active',
    NOW() - INTERVAL '23 hours'
  ),
  (
    6743,
    'Samuel Torres',
    'samuel.torres@example.com',
    'VN-4378',
    'BlueStone Dynamics',
    'pending',
    NOW() - INTERVAL '8 days'
  ),
  (
    5381,
    'Luna Cox',
    'luna.cox@example.com',
    'VN-6053',
    'SummitStone Group',
    'active',
    NOW() - INTERVAL '3 days'
  ),
  (
    8206,
    'Joseph Flores',
    'joseph.flores@example.com',
    'VN-7192',
    'ClearEdge Retail',
    'inactive',
    NOW() - INTERVAL '9 hours'
  ),
  (
    2975,
    'Aria Gonzales',
    'aria.gonzales@example.com',
    'VN-4627',
    'IronPath Consulting',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    6501,
    'Wyatt Bell',
    'wyatt.bell@example.com',
    'VN-8840',
    'PeakStone Ventures',
    'pending',
    NOW() - INTERVAL '12 days'
  ),
  (
    7132,
    'Hannah Ward',
    'hannah.ward@example.com',
    'VN-5738',
    'NorthWave Solutions',
    'active',
    NOW() - INTERVAL '6 days'
  ),
  (
    8894,
    'Gabriel Murphy',
    'gabriel.murphy@example.com',
    'VN-2481',
    'SummitEdge Corp',
    'inactive',
    NOW() - INTERVAL '3 days'
  ),
  (
    4219,
    'Layla Foster',
    'layla.foster@example.com',
    'VN-3260',
    'BlueSky Logistics',
    'active',
    NOW() - INTERVAL '17 hours'
  ),
  (
    9328,
    'Anthony Howard',
    'anthony.howard@example.com',
    'VN-9072',
    'ClearPath Ventures',
    'pending',
    NOW() - INTERVAL '10 days'
  ),
  (
    5861,
    'Victoria Allen',
    'victoria.allen@example.com',
    'VN-1178',
    'IronCrest Retailers',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    4796,
    'Leo Cook',
    'leo.cook@example.com',
    'VN-7365',
    'BrightPoint Systems',
    'inactive',
    NOW() - INTERVAL '4 hours'
  ),
  (
    7620,
    'Sofia Ward',
    'sofia.ward@example.com',
    'VN-6529',
    'SummitVision Global',
    'active',
    NOW() - INTERVAL '5 days'
  ),
  (
    8539,
    'Elena Diaz',
    'elena.diaz@example.com',
    'VN-2897',
    'ClearStone Enterprises',
    'pending',
    NOW() - INTERVAL '7 days'
  ),
  (
    6345,
    'Andrew Powell',
    'andrew.powell@example.com',
    'VN-9462',
    'CrownStone Logistics',
    'active',
    NOW() - INTERVAL '13 hours'
  ),
  (
    9058,
    'Brooklyn Hughes',
    'brooklyn.hughes@example.com',
    'VN-5179',
    'NextGen Partners',
    'inactive',
    NOW() - INTERVAL '11 days'
  ),
  (
    3127,
    'Mila Richardson',
    'mila.richardson@example.com',
    'VN-2834',
    'SummitBridge Ltd',
    'active',
    NOW() - INTERVAL '1 day'
  ),
  (
    7804,
    'Eleanor Wood',
    'eleanor.wood@example.com',
    'VN-6035',
    'BlueHaven Solutions',
    'pending',
    NOW() - INTERVAL '6 days'
  ),
  (
    5279,
    'Isaac Foster',
    'isaac.foster@example.com',
    'VN-8129',
    'IronPeak Ventures',
    'active',
    NOW() - INTERVAL '21 hours'
  ),
  (
    6897,
    'Hazel Murphy',
    'hazel.murphy@example.com',
    'VN-1370',
    'BrightWave Global',
    'inactive',
    NOW() - INTERVAL '3 days'
  ),
  (
    4982,
    'Nathan Clark',
    'nathan.clark@example.com',
    'VN-7294',
    'SummitPath Corp',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    7410,
    'Zoey Hall',
    'zoey.hall@example.com',
    'VN-2857',
    'ClearVision Enterprises',
    'pending',
    NOW() - INTERVAL '8 days'
  ),
  (
    8926,
    'Eli Rogers',
    'eli.rogers@example.com',
    'VN-9004',
    'CrownPoint Tech',
    'active',
    NOW() - INTERVAL '9 hours'
  ),
  (
    5369,
    'Aurora Bailey',
    'aurora.bailey@example.com',
    'VN-6745',
    'NextHorizon Retail',
    'inactive',
    NOW() - INTERVAL '4 days'
  ),
  (
    6185,
    'Hunter Allen',
    'hunter.allen@example.com',
    'VN-4219',
    'SummitEdge Ltd',
    'active',
    NOW() - INTERVAL '12 hours'
  ),
  (
    3591,
    'Savannah Torres',
    'savannah.torres@example.com',
    'VN-8156',
    'BlueCrest Ventures',
    'pending',
    NOW() - INTERVAL '13 days'
  ),
  (
    7038,
    'Julian Wright',
    'julian.wright@example.com',
    'VN-5096',
    'BrightHaven Traders',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    9217,
    'Nora Hughes',
    'nora.hughes@example.com',
    'VN-7390',
    'ClearPeak Systems',
    'inactive',
    NOW() - INTERVAL '5 days'
  ),
  (
    4880,
    'Levi Price',
    'levi.price@example.com',
    'VN-9817',
    'IronEdge Corp',
    'active',
    NOW() - INTERVAL '14 hours'
  ),
  (
    6471,
    'Ellie Green',
    'ellie.green@example.com',
    'VN-2368',
    'SummitPoint Enterprises',
    'pending',
    NOW() - INTERVAL '3 days'
  ),
  (
    8194,
    'Caleb Perez',
    'caleb.perez@example.com',
    'VN-4609',
    'NorthStone Retailers',
    'active',
    NOW() - INTERVAL '7 days'
  ),
  (
    3785,
    'Aubrey Ramirez',
    'aubrey.ramirez@example.com',
    'VN-6781',
    'BlueGate Logistics',
    'inactive',
    NOW() - INTERVAL '16 hours'
  ),
  (
    5943,
    'Dylan Adams',
    'dylan.adams@example.com',
    'VN-3197',
    'NextVision Global',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    7489,
    'Addison Cooper',
    'addison.cooper@example.com',
    'VN-8271',
    'CrownWave Partners',
    'pending',
    NOW() - INTERVAL '11 days'
  ),
  (
    8124,
    'Landon Brooks',
    'landon.brooks@example.com',
    'VN-5920',
    'IronStone Enterprises',
    'active',
    NOW() - INTERVAL '20 hours'
  ),
  (
    4597,
    'Stella Jenkins',
    'stella.jenkins@example.com',
    'VN-9138',
    'BrightStone Solutions',
    'inactive',
    NOW() - INTERVAL '3 days'
  ),
  (
    6942,
    'Jonathan Bell',
    'jonathan.bell@example.com',
    'VN-6472',
    'ClearHaven Group',
    'active',
    NOW() - INTERVAL '6 days'
  ),
  (
    8351,
    'Paisley Scott',
    'paisley.scott@example.com',
    'VN-7538',
    'SummitVision Tech',
    'pending',
    NOW() - INTERVAL '4 days'
  ),
  (
    9106,
    'Christian Murphy',
    'christian.murphy@example.com',
    'VN-8729',
    'IronPath Ventures',
    'active',
    NOW() - INTERVAL '8 hours'
  ),
  (
    3215,
    'Camila Rogers',
    'camila.rogers@example.com',
    'VN-2861',
    'NextCrest Retail',
    'inactive',
    NOW() - INTERVAL '15 days'
  ),
  (
    7896,
    'Aaron Russell',
    'aaron.russell@example.com',
    'VN-5489',
    'BrightGate Enterprises',
    'active',
    NOW() - INTERVAL '1 day'
  ),
  (
    4673,
    'Penelope Hayes',
    'penelope.hayes@example.com',
    'VN-9732',
    'NorthVision Partners',
    'pending',
    NOW() - INTERVAL '5 days'
  ),
  (
    6208,
    'Christopher Powell',
    'christopher.powell@example.com',
    'VN-3608',
    'ClearEdge Systems',
    'active',
    NOW() - INTERVAL '13 hours'
  ),
  (
    8569,
    'Samantha Jenkins',
    'samantha.jenkins@example.com',
    'VN-4205',
    'SummitPoint Ltd',
    'inactive',
    NOW() - INTERVAL '9 days'
  ),
  (
    9321,
    'Ezekiel Foster',
    'ezekiel.foster@example.com',
    'VN-7506',
    'IronBridge Retail',
    'active',
    NOW() - INTERVAL '4 hours'
  ),
  (
    5147,
    'Aurora Ramirez',
    'aurora.ramirez@example.com',
    'VN-8294',
    'BlueWave Dynamics',
    'pending',
    NOW() - INTERVAL '6 days'
  ),
  (
    6028,
    'Adrian Hughes',
    'adrian.hughes@example.com',
    'VN-1985',
    'CrownVision Corp',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    7493,
    'Riley Ward',
    'riley.ward@example.com',
    'VN-6329',
    'BrightCrest Partners',
    'inactive',
    NOW() - INTERVAL '18 hours'
  ),
  (
    8951,
    'Naomi Torres',
    'naomi.torres@example.com',
    'VN-9054',
    'NorthHaven Solutions',
    'active',
    NOW() - INTERVAL '7 days'
  ),
  (
    3817,
    'Elias King',
    'elias.king@example.com',
    'VN-4723',
    'ClearStone Consulting',
    'pending',
    NOW() - INTERVAL '5 days'
  ),
  (
    5607,
    'Autumn Scott',
    'autumn.scott@example.com',
    'VN-6547',
    'SummitVision Retail',
    'active',
    NOW() - INTERVAL '10 hours'
  ),
  (
    6342,
    'Nicholas Ross',
    'nicholas.ross@example.com',
    'VN-7921',
    'BlueHaven Ventures',
    'inactive',
    NOW() - INTERVAL '11 days'
  ),
  (
    7199,
    'Aaliyah Howard',
    'aaliyah.howard@example.com',
    'VN-8905',
    'IronVision Tech',
    'active',
    NOW() - INTERVAL '2 days'
  ),
  (
    8929,
    'Dominic Ward',
    'dominic.ward@example.com',
    'VN-2138',
    'BrightEdge Systems',
    'pending',
    NOW() - INTERVAL '6 days'
  );
