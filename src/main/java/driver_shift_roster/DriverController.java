
package driver_shift_roster;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import jakarta.validation.Valid;

@Controller
public class DriverController {

    private final DriverRepository driverRepository;

    public DriverController(DriverRepository driverRepository) {
        this.driverRepository = driverRepository;
    }

    @GetMapping("/drivers")
    public String listDrivers(Model model) {
        model.addAttribute("drivers", driverRepository.findAll());
        model.addAttribute("driver", new Driver());
        return "drivers";
    }

    @PostMapping("/drivers")
    public String addDriver(
            @Valid @ModelAttribute("driver") Driver driver,
            BindingResult result,
            Model model,
            RedirectAttributes redirectAttributes) {

        if (driverRepository.existsByPhone(driver.getPhone())) {
            result.rejectValue("phone", "duplicate",
                    "This phone number is already registered");
        }

        if (result.hasErrors()) {
            model.addAttribute("drivers", driverRepository.findAll());
            return "drivers";
        }

        driverRepository.save(driver);
        redirectAttributes.addFlashAttribute(
                "successMessage", "Driver added successfully!");

        return "redirect:/drivers";
    }
}
