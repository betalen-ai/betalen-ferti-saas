import { allocatePayment, calcCreditTotal, calcSpotTotal, monthsBetween } from './interest.util';

describe('shop billing calculations', () => {
  it('subtracts fixed and percentage discounts without allowing a negative total', () => {
    expect(calcSpotTotal(1000, 50)).toBe(950);
    expect(calcSpotTotal(1000, 5, 'percent')).toBe(950);
    expect(calcSpotTotal(1000, 2000)).toBe(0);
  });

  it('calculates simple monthly interest on a credit bill', () => {
    expect(calcCreditTotal(1000, 1, 1)).toEqual({ principal: 1000, interest: 10, total: 1010, balance: 1010 });
    expect(calcCreditTotal(1000, 1, 6)).toEqual({ principal: 1000, interest: 60, total: 1060, balance: 1060 });
    expect(calcCreditTotal(1000, 0.5, 6).total).toBe(1030);
  });

  it('calculates interest on the credit portion of a part payment', () => {
    expect(calcCreditTotal(1000, 1, 4, 400)).toEqual({ principal: 600, interest: 24, total: 1024, balance: 624 });
  });

  it('calculates months from the selected due date rounded to one decimal place', () => {
    expect(monthsBetween('2026-01-01', '2026-03-02')).toBe(2);
    expect(monthsBetween('2026-01-01', '2026-01-01')).toBe(0);
    expect(monthsBetween('not-a-date', '2026-01-01')).toBe(0);
  });

  it('allocates received payments oldest-first and pays interest before principal', () => {
    expect(allocatePayment(100, [
      { billId: 'newer', date: '2026-02-01', interestDue: 5, principalDue: 45 },
      { billId: 'older', date: '2026-01-01', interestDue: 10, principalDue: 90 }
    ])).toEqual([
      { billId: 'older', interestPaid: 10, principalPaid: 90, amount: 100 }
    ]);
    expect(allocatePayment(20, [
      { billId: 'older', date: '2026-01-01', interestDue: 10, principalDue: 90 }
    ])).toEqual([{ billId: 'older', interestPaid: 10, principalPaid: 10, amount: 20 }]);
  });
});
