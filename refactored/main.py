"""
Main Orchestration - Clean, Simple Entry Point
All complexity is abstracted into department schedulers
"""

from datetime import datetime
from data_loader import DataLoader
from departments.packing import SmallPackingScheduler, LargePackingScheduler
# from departments.bin_filling import BinFillingScheduler
# from departments.rack_filling import RackFillingScheduler
# from departments.freight import MainFreightScheduler, AuxFreightScheduler
# from departments.shipping import ParcelShippingScheduler
# from departments.will_call import WillCallScheduler


def main():
    """
    Main scheduling workflow - now under 100 lines!
    """

    # Configuration
    target_date = datetime(2025, 11, 5)

    print("="*80)
    print(f"GENERATING SCHEDULES FOR {target_date.strftime('%A, %B %d, %Y')}")
    print("="*80)

    # Initialize data loader (single source of truth)
    data_loader = DataLoader(target_date)

    # Schedule each department
    results = {}

    # Bin Filling
    # bf_scheduler = BinFillingScheduler(target_date, data_loader)
    # results['bin_filling'] = bf_scheduler.schedule()

    # Rack Filling
    # rf_scheduler = RackFillingScheduler(target_date, data_loader)
    # results['rack_filling'] = rf_scheduler.schedule()

    # Small Packing
    sp_scheduler = SmallPackingScheduler(target_date, data_loader)
    results['small_packing'] = sp_scheduler.schedule()

    # Large Packing
    lp_scheduler = LargePackingScheduler(target_date, data_loader)
    results['large_packing'] = lp_scheduler.schedule()

    # Parcel Shipping
    # ps_scheduler = ParcelShippingScheduler(target_date, data_loader)
    # results['parcel_shipping'] = ps_scheduler.schedule()

    # Will Call
    # wc_scheduler = WillCallScheduler(target_date, data_loader)
    # results['will_call'] = wc_scheduler.schedule()

    # Main Freight
    # mf_scheduler = MainFreightScheduler(target_date, data_loader)
    # results['main_freight'] = mf_scheduler.schedule()

    # AUX Freight
    # af_scheduler = AuxFreightScheduler(target_date, data_loader)
    # results['aux_freight'] = af_scheduler.schedule()

    # Export to Excel and HTML
    # from exporters import export_to_excel, export_to_html
    # export_to_excel(target_date, results)
    # export_to_html(target_date, results)

    print("\n" + "="*80)
    print("✅ SCHEDULING COMPLETE")
    print("="*80)

    return results


if __name__ == "__main__":
    results = main()
