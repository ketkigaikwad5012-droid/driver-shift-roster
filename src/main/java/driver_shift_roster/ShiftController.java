
package driver_shift_roster;

import java.time.LocalDate;
import java.time.LocalTime;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class ShiftController {

    private final ShiftRepository shiftRepository;
    private final DriverRepository driverRepository;

    public ShiftController(
            ShiftRepository shiftRepository,
            DriverRepository driverRepository) {
        this.shiftRepository = shiftRepository;
        this.driverRepository = driverRepository;
    }

    @GetMapping("/shifts")
    public String listShifts(Model model) {
        model.addAttribute("shifts", shiftRepository.findAll());
        model.addAttribute("drivers", driverRepository.findAll());
        model.addAttribute("shift", new Shift());
        model.addAttribute("today", LocalDate.now());

        return "shifts";
    }

    @PostMapping("/shifts")
    public String addShift(
            @RequestParam Long driverId,
            @RequestParam LocalDate shiftDate,
            @RequestParam LocalTime startTime,
            @RequestParam LocalTime endTime,
            RedirectAttributes redirectAttributes) {

        // Validate the time range
        if (!endTime.isAfter(startTime)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage",
                    "End time must be later than start time.");
            return "redirect:/shifts";
        }

        // Prevent scheduling shifts in the past
        if (shiftDate.isBefore(LocalDate.now())) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage",
                    "Shift date cannot be in the past.");
            return "redirect:/shifts";
        }

        // Find the selected driver
        Driver driver = driverRepository.findById(driverId)
                .orElseThrow(() -> new IllegalArgumentException("Driver not found"));

        // Check driver availability
        if (!driver.isAvailable()) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage",
                    "This driver is currently unavailable.");
            return "redirect:/shifts";
        }

        // Check for overlapping shifts
        boolean overlappingShift = shiftRepository
                .existsByDriverIdAndShiftDateAndStartTimeLessThanAndEndTimeGreaterThan(
                        driverId,
                        shiftDate,
                        endTime,
                        startTime);

        if (overlappingShift) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage",
                    "This driver already has a shift during that time.");
            return "redirect:/shifts";
        }

        // Create and save the shift
        Shift shift = new Shift();
        shift.setDriver(driver);
        shift.setShiftDate(shiftDate);
        shift.setStartTime(startTime);
        shift.setEndTime(endTime);

        shiftRepository.save(shift);

        // Show the success message
        redirectAttributes.addFlashAttribute(
                "successMessage",
                "Shift scheduled successfully!");

        return "redirect:/shifts";
    }
}
