in D0, #0

  in D1, #0

  in D2, #0

  in D3, #0

  add.l D0, D2

  bcc no_carry

  add.l #1, D1

  no_carry:

  add.l D1, D3

  out D2, #1

  out D3, #1

  hlt